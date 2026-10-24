"""Google Cloud adapters. Imported only when AMAZING_TTS_CLOUD=1."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
from google.cloud import firestore, storage, tasks_v2
from google.api_core.exceptions import AlreadyExists, NotFound
from .storage import Library, digest
from .scraper import Scraper
from .llm import Gemini
from .audio import Renderer, export_mp3
from .pipeline import process, accept_script
from .models import Script

EDITION = os.getenv("AUDIOBOOK_EDITION", "v1")


class Objects:
    def __init__(self):
        self.client = storage.Client()
        self.bucket = self.client.bucket(os.environ["AUDIO_BUCKET"])

    def get_audio(self, key, target):
        try:
            self.bucket.blob(f"editions/{EDITION}/segments/{key}.wav").download_to_filename(str(target))
        except NotFound:
            return False
        return True

    def put_audio(self, key, path):
        blob = self.bucket.blob(f"editions/{EDITION}/segments/{key}.wav")
        # Conditional create prevents accidental overwrites of shared content-addressed data.
        try:
            blob.upload_from_filename(str(path), content_type="audio/wav", if_generation_match=0)
        except Exception as exc:
            from google.api_core.exceptions import PreconditionFailed
            if not isinstance(exc, PreconditionFailed):
                raise

    def prefix(self, bid):
        return f"editions/{EDITION}/books/{bid}/"

    def restore(self, bid, book):
        for blob in self.client.list_blobs(self.bucket, prefix=self.prefix(bid)):
            rel = blob.name[len(self.prefix(bid)):]
            # Restore state only; audio is fetched lazily by content hash.
            if not rel.endswith(".json") or ".." in Path(rel).parts or Path(rel).is_absolute():
                continue
            path = book.path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(path))

    def save(self, bid, book):
        # Caller must hold the distributed book lease. JSON is replaceable checkpoint state.
        for path in book.path.rglob("*.json"):
            blob = self.bucket.blob(self.prefix(bid) + path.relative_to(book.path).as_posix())
            blob.upload_from_filename(str(path), content_type="application/json")

    def upload_chapter(self, bid, n, audio):
        key = self.prefix(bid) + f"playback/{n:06d}-{audio.stem}.mp3"
        blob = self.bucket.blob(key)
        if not blob.exists():
            blob.upload_from_filename(str(audio), content_type="audio/mpeg", if_generation_match=0)
        return key

    def json(self, bid, relative):
        try:
            return json.loads(self.bucket.blob(self.prefix(bid)+relative).download_as_text())
        except NotFound:
            return None

    def signed_audio(self, key):
        import google.auth
        from google.auth.transport.requests import Request
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(Request())
        return self.bucket.blob(key).generate_signed_url(
            version="v4", expiration=timedelta(hours=2), method="GET",
            service_account_email=os.environ["SIGNING_SERVICE_ACCOUNT"], access_token=credentials.token)


class Cloud:
    def __init__(self):
        self.db, self.objects = firestore.Client(), Objects()
        self.jobs = self.db.collection("amazing_tts_books")

    def catalog(self):
        return [{"id": doc.id, **doc.to_dict()} for doc in self.jobs.order_by("updated", direction=firestore.Query.DESCENDING).limit(100).stream()]

    def get(self, bid):
        doc = self.jobs.document(bid).get()
        if not doc.exists:
            raise ValueError("Unknown audiobook")
        return {"id": bid, **doc.to_dict()}

    def reserve(self, model, tokens):
        from zoneinfo import ZoneInfo
        day = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
        ref = self.db.collection("amazing_tts_quota").document(digest([model, day]))
        now = time.time()
        @firestore.transactional
        def take(tx):
            doc = ref.get(transaction=tx)
            d = doc.to_dict() if doc.exists else {"count": 0, "recent": []}
            recent = [r for r in d["recent"] if r["at"] > now-60]
            if d["count"] >= int(os.getenv("GEMINI_DAILY_BUDGET", "480")):
                raise RuntimeError("Daily shared Gemini budget reached; resume after midnight Pacific")
            if len(recent) >= int(os.getenv("GEMINI_RPM", "5")) or sum(r["tokens"] for r in recent)+tokens > int(os.getenv("GEMINI_TPM", "100000")):
                raise RuntimeError("Shared minute budget reached; resume in a minute")
            recent.append({"at": now, "tokens": tokens})
            tx.set(ref, {"count": d["count"]+1, "recent": recent, "model": model, "day": day})
        take(self.db.transaction())

    def request(self, url, target, uid):
        bid = digest([EDITION, url])[:32]
        ref = self.jobs.document(bid)
        now = time.time()
        # Bound generation by user/day, independently of the shared provider quota.
        user_ref = self.db.collection("amazing_tts_users").document(digest([uid, datetime.now(timezone.utc).date().isoformat()]))
        @firestore.transactional
        def create(tx):
            snapshot = ref.get(transaction=tx)
            usage = user_ref.get(transaction=tx)
            job = snapshot.to_dict() if snapshot.exists else None
            if job and job.get("ready", 0) >= target:
                return job
            if job and job["state"] in {"queued", "running"}:
                return job
            if job and job["state"] == "needs_review":
                return job
            count = usage.to_dict().get("requests", 0) if usage.exists else 0
            if count >= 3:
                raise ValueError("Daily generation request limit reached (3). Saved audiobooks remain available.")
            job = job or {"url": url, "title": url.rsplit("/", 1)[-1].replace("-", " ").title(), "owner": uid, "ready": 0, "next": 1, "edition": EDITION}
            job.update(state="queued", target=max(target, job.get("target", 0)), updated=now, lease_until=0, run_id=uuid.uuid4().hex, error=None)
            tx.set(ref, job)
            tx.set(user_ref, {"requests": count+1})
            return job
        job = create(self.db.transaction())
        if job["state"] == "queued":
            self.enqueue(bid, job["next"], job["run_id"])
        return {"id": bid, **job}

    def enqueue(self, bid, chapter, run_id):
        client = tasks_v2.CloudTasksClient()
        queue = client.queue_path(os.environ["GOOGLE_CLOUD_PROJECT"], os.environ.get("CLOUD_REGION", "us-central1"), os.environ.get("TASK_QUEUE", "amazing-tts"))
        task = {"name": queue + "/tasks/" + f"{bid}-{run_id}-{chapter}",
                "dispatch_deadline": {"seconds": 1800},
                "http_request": {"http_method": tasks_v2.HttpMethod.POST, "url": os.environ["WORKER_URL"] + "/internal/chapter",
                                 "headers": {"Content-Type": "application/json"},
                                 "body": json.dumps({"book_id": bid, "chapter": chapter, "run_id": run_id}).encode(),
                                 "oidc_token": {"service_account_email": os.environ["TASK_SERVICE_ACCOUNT"], "audience": os.environ["WORKER_URL"]}}}
        try:
            client.create_task(parent=queue, task=task)
        except AlreadyExists:
            pass

    def lease(self, bid, chapter, run_id):
        ref, now = self.jobs.document(bid), time.time()
        token = uuid.uuid4().hex
        @firestore.transactional
        def claim(tx):
            job = ref.get(transaction=tx).to_dict()
            if job["run_id"] != run_id or job["state"] not in {"queued", "running"} or job["next"] != chapter:
                return None
            if job.get("lease_until", 0) > now:
                raise RuntimeError("Another worker owns this chapter lease")
            tx.update(ref, {"state": "running", "lease_until": now+2100, "lease_token": token, "updated": now})
            return job
        return claim(self.db.transaction()), token

    def finish(self, bid, token, updates):
        ref = self.jobs.document(bid)
        @firestore.transactional
        def update(tx):
            doc = ref.get(transaction=tx).to_dict()
            if doc.get("lease_token") != token:
                raise RuntimeError("Worker lease no longer belongs to this request")
            tx.update(ref, {**updates, "lease_until": 0, "updated": time.time()})
        update(self.db.transaction())

    def work(self, bid, chapter, run_id):
        job, token = self.lease(bid, chapter, run_id)
        if job is None:
            # Recover a crash after state commit but before scheduling the next chapter.
            current = self.get(bid)
            if current["state"] == "queued" and current["run_id"] == run_id:
                self.enqueue(bid, current["next"], run_id)
            return
        with tempfile.TemporaryDirectory(prefix="amazing-tts-") as directory:
            library = Library(Path(directory))
            book = library.book(job["url"])
            self.objects.restore(bid, book)
            try:
                sources = list(Scraper().download(book, limit=1, start=chapter))
                if not sources:
                    self.finish(bid, token, {"state": "complete", "target": chapter-1})
                    return
                source = sources[0]
                # A cached validated script requires no Gemini configuration or request.
                llm = None
                if book.read(book.chapter_name(chapter) + "/script.json") is None:
                    llm = Gemini(library, reserve=lambda tokens: self.reserve(os.environ["GEMINI_MODEL"], tokens))
                result = process(book, source, llm, Renderer(library, remote=self.objects, deadline=time.monotonic()+1200))
                self.objects.save(bid, book)
                if result["state"] == "needs_review":
                    self.finish(bid, token, {"state": "needs_review", "warnings": result["warnings"], "title": book.read("book.json")["title"]})
                    return
                mp3 = export_mp3(Path(result["audio"]))
                key = self.objects.upload_chapter(bid, chapter, mp3)
                manifest = book.read(book.chapter_name(chapter)+"/audio.json")
                self.jobs.document(bid).collection("chapters").document(f"{chapter:06d}").set({"number": chapter, "title": source["title"], "key": key, "duration_seconds": manifest["duration_seconds"]})
                state = "queued" if chapter < job["target"] and source["next_url"] else "complete"
                self.finish(bid, token, {"state": state, "next": chapter+1, "ready": chapter, "title": book.read("book.json")["title"], "warnings": []})
            except (ValueError, RuntimeError) as exc:
                # Persist candidate and cast even on validation/quotas; no raw provider response or secrets in errors.
                self.objects.save(bid, book)
                self.finish(bid, token, {"state": "paused", "error": str(exc)[:500]})
                return
            if state == "queued":
                self.enqueue(bid, chapter+1, run_id)

    def review(self, bid, uid, admin, script_dict):
        job = self.get(bid)
        if uid != job["owner"] and not admin:
            raise PermissionError("Only the requester or an administrator can approve this shared audiobook")
        if job["state"] not in {"needs_review", "paused"}:
            raise ValueError("This audiobook is not awaiting review")
        # Use the same book lease to serialize review and generation.
        ref = self.jobs.document(bid)
        token = uuid.uuid4().hex
        @firestore.transactional
        def claim(tx):
            live = ref.get(transaction=tx).to_dict()
            if live["state"] not in {"needs_review", "paused"} or live.get("lease_until", 0) > time.time():
                raise ValueError("Book changed or is already being reviewed")
            tx.update(ref, {"lease_token": token, "lease_until": time.time()+300})
        claim(self.db.transaction())
        try:
            with tempfile.TemporaryDirectory() as directory:
                book = Library(Path(directory)).book(job["url"])
                self.objects.restore(bid, book)
                source = book.read(book.chapter_name(job["next"])+"/source.json")
                if not source:
                    raise ValueError("No chapter source to review")
                accept_script(book, source, Script.model_validate(script_dict), approve=True)
                self.objects.save(bid, book)
            run_id = uuid.uuid4().hex
            self.finish(bid, token, {"state": "queued", "run_id": run_id, "error": None, "warnings": []})
            self.enqueue(bid, job["next"], run_id)
        except Exception:
            self.finish(bid, token, {})
            raise
