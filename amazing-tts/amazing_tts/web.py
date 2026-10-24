from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import re
import threading
import time
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .storage import Library, DEFAULT_DATA, digest
from .scraper import book_url, Scraper
from .pipeline import process, accept_script
from .audio import Renderer, export_mp3
from .models import Script
from .llm import Gemini

CLOUD = os.getenv("AMAZING_TTS_CLOUD") == "1"
WORKER = os.getenv("SERVICE_MODE") == "worker"
ROOT = Path(os.getenv("AMAZING_TTS_DATA", str(DEFAULT_DATA)))
executor = ThreadPoolExecutor(max_workers=1)
local_guard = threading.Lock()


@asynccontextmanager
async def lifespan(app):
    yield
    executor.shutdown(wait=False, cancel_futures=True)


app = FastAPI(title="Amazing TTS", lifespan=lifespan)


def library():
    return Library(ROOT)


def cloud():
    from .cloud import Cloud
    return Cloud()


def public():
    if WORKER:
        raise HTTPException(404)


def identity(request: Request):
    public()
    if not CLOUD:
        return {"uid": "local", "admin": True}
    from firebase_admin import auth, initialize_app, get_app
    try:
        get_app()
    except ValueError:
        initialize_app()
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    try:
        return auth.verify_id_token(token, check_revoked=True)
    except Exception:
        raise HTTPException(401, "Sign in to request an audiobook") from None


class GenerationRequest(BaseModel):
    url: str = Field(max_length=300)
    chapters: int = Field(default=1, ge=1, le=1000)


class ReviewRequest(BaseModel):
    script: dict


def local_book(bid):
    if not re.fullmatch(r"[a-f0-9]{20}", bid):
        raise HTTPException(404)
    path = library().root / "novels" / bid / "book.json"
    if not path.exists():
        raise HTTPException(404)
    return library().book(json.loads(path.read_text())["url"])


def local_job(book):
    return book.read("job.json", {"state": "imported", "ready": 0, "target": 1})


def run_local(url, target):
    book = library().book(url)
    try:
        with book.lock():
            book.write("job.json", {**local_job(book), "state": "running", "target": target})
            llm = None
            for source in Scraper().download(book, target):
                if book.read(book.chapter_name(source["number"])+"/script.json") is None and llm is None:
                    llm = Gemini(library())
                result = process(book, source, llm, Renderer(library()))
                if result["state"] == "needs_review":
                    book.write("job.json", {**local_job(book), "state": "needs_review", "next": source["number"], "warnings": result["warnings"]})
                    return
                export_mp3(Path(result["audio"]))
                book.write("job.json", {**local_job(book), "ready": source["number"], "next": source["number"]+1})
            book.write("job.json", {**local_job(book), "state": "complete"})
    except Exception as exc:
        book.write("job.json", {**local_job(book), "state": "paused", "error": str(exc)[:500]})


@app.get("/", dependencies=[Depends(public)])
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/config", dependencies=[Depends(public)])
def config():
    return {"cloud": CLOUD, "firebase": {"apiKey": os.getenv("FIREBASE_API_KEY", ""), "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""), "projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "")}}


@app.get("/api/books", dependencies=[Depends(public)])
def catalog():
    if CLOUD:
        # Expose public catalog fields only; no requester identities or internal leases.
        return [{k: v for k, v in j.items() if k in {"id", "title", "url", "state", "ready", "target", "error", "warnings"}} for j in cloud().catalog()]
    result = []
    for path in library().books():
        meta = json.loads(path.read_text())
        book = library().book(meta["url"])
        result.append({"id": path.parent.name, "title": meta["title"], "url": meta["url"], **local_job(book)})
    return result


@app.post("/api/books")
def generate(body: GenerationRequest, user=Depends(identity)):
    try:
        url = book_url(body.url)
        if CLOUD:
            j = cloud().request(url, body.chapters, user["uid"])
            return {"id": j["id"], "state": j["state"], "ready": j["ready"]}
        book = library().book(url)
        with local_guard:
            job = local_job(book)
            if job.get("ready", 0) >= body.chapters:
                return {"id": book.path.name, **job}
            if job["state"] not in {"queued", "running", "needs_review"}:
                # Make it visible immediately; metadata is replaced after real discovery.
                if not book.read("book.json"):
                    Scraper().discover(book)
                book.write("job.json", {**job, "state": "queued", "target": body.chapters})
                executor.submit(run_local, url, body.chapters)
        return {"id": book.path.name, **local_job(book)}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc)) from None


@app.get("/api/books/{bid}", dependencies=[Depends(public)])
def details(bid: str):
    if CLOUD:
        c = cloud()
        try:
            job = c.get(bid)
        except ValueError:
            raise HTTPException(404) from None
        chapters = [doc.to_dict() for doc in c.jobs.document(bid).collection("chapters").order_by("number").stream()]
        for chapter in chapters:
            chapter.pop("key", None)
            chapter["audio"] = f'/api/books/{bid}/audio/{chapter["number"]}'
        cast = c.objects.json(bid, "cast.json") or {}
        return {"id": bid, **{k: job.get(k) for k in ["title", "url", "state", "ready", "target", "error", "warnings"]}, "chapters": chapters, "cast": cast}
    book = local_book(bid)
    chapters = []
    for path in book.chapters():
        src = json.loads(path.read_text())
        manifest = book.read(book.chapter_name(src["number"])+"/audio.json")
        if manifest:
            chapters.append({"number": src["number"], "title": src["title"], "duration_seconds": manifest["duration_seconds"], "audio": f'/api/books/{bid}/audio/{src["number"]}'})
    return {"id": bid, **book.read("book.json"), **local_job(book), "chapters": chapters, "cast": book.read("cast.json", {})}


@app.get("/api/books/{bid}/audio/{chapter}", dependencies=[Depends(public)])
def playback(bid: str, chapter: int):
    if chapter < 1:
        raise HTTPException(404)
    if CLOUD:
        from fastapi.responses import RedirectResponse
        c = cloud()
        doc = c.jobs.document(bid).collection("chapters").document(f"{chapter:06d}").get()
        if not doc.exists:
            raise HTTPException(404)
        return RedirectResponse(c.objects.signed_audio(doc.to_dict()["key"]))
    book = local_book(bid)
    base = book.chapter_name(chapter)
    m = book.read(base+"/audio.json")
    if not m:
        raise HTTPException(404)
    path = book.path / base / m["file"]
    mp3 = path.with_suffix(".mp3")
    return FileResponse(mp3 if mp3.exists() else path, media_type="audio/mpeg" if mp3.exists() else "audio/wav")


@app.get("/api/books/{bid}/review")
def get_review(bid: str, user=Depends(identity)):
    if CLOUD:
        c = cloud()
        job = c.get(bid)
        if user["uid"] != job["owner"] and not user.get("admin"):
            raise HTTPException(403)
        n = job["next"]
        source = c.objects.json(bid, f"chapters/{n:06d}/source.json")
        script = c.objects.json(bid, f"chapters/{n:06d}/script.json")
        candidate = c.objects.json(bid, f"chapters/{n:06d}/candidate.json")
    else:
        book = local_book(bid)
        n = local_job(book).get("next", 1)
        source = book.read(book.chapter_name(n)+"/source.json")
        script = book.read(book.chapter_name(n)+"/script.json")
        candidate = book.read(book.chapter_name(n)+"/candidate.json")
    return {"chapter": n, "source": source, "script": script["script"] if script else candidate}


@app.post("/api/books/{bid}/review")
def approve(bid: str, body: ReviewRequest, user=Depends(identity)):
    try:
        if CLOUD:
            cloud().review(bid, user["uid"], user.get("admin", False), body.script)
        else:
            book = local_book(bid)
            with book.lock():
                job = local_job(book)
                if job["state"] not in {"needs_review", "paused"}:
                    raise ValueError("Book is not awaiting review")
                source = book.read(book.chapter_name(job.get("next", 1))+"/source.json")
                if not source:
                    raise ValueError("No source to review")
                accept_script(book, source, Script.model_validate(body.script), approve=True)
                book.write("job.json", {**job, "state": "queued", "error": None})
            executor.submit(run_local, book.url, job["target"])
        return {"ok": True}
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from None
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc)) from None


class TaskRequest(BaseModel):
    book_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    chapter: int = Field(ge=1)
    run_id: str = Field(pattern=r"^[a-f0-9]{32}$")


@app.post("/internal/chapter")
def worker(body: TaskRequest):
    # This route exists only on the PRIVATE Cloud Run worker service.
    # Cloud Run IAM validates Cloud Tasks' OIDC identity before reaching the container.
    if not CLOUD or not WORKER:
        raise HTTPException(404)
    try:
        cloud().work(body.book_id, body.chapter, body.run_id)
    except Exception:
        raise HTTPException(503, "Worker interrupted; Cloud Tasks will retry using saved checkpoints") from None
    return {"ok": True}
