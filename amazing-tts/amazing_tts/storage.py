from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from filelock import FileLock

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


class Library:
    def __init__(self, root: Path = DEFAULT_DATA):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def book(self, url: str):
        return Book(self.root / "novels" / digest(url)[:20], url)

    def books(self):
        return sorted((self.root / "novels").glob("*/book.json"))

    def budget(self, model: str, daily: int, rpm: int, tpm: int, tokens: int):
        """Reserve before network; shared by all novels/processes under this data root."""
        import datetime
        import time
        from zoneinfo import ZoneInfo
        if min(daily, rpm, tpm) < 1:
            raise ValueError("Quota limits must be positive")
        day = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
        now = time.time()
        with sqlite3.connect(self.root / "quota.sqlite", timeout=30) as db:
            db.execute("CREATE TABLE IF NOT EXISTS calls (model TEXT, day TEXT, at REAL, tokens INTEGER)")
            db.execute("BEGIN IMMEDIATE")
            count = db.execute("SELECT count(*) FROM calls WHERE model=? AND day=?", (model, day)).fetchone()[0]
            recent = db.execute("SELECT count(*), coalesce(sum(tokens),0) FROM calls WHERE model=? AND at>?", (model, now-60)).fetchone()
            if count >= daily:
                raise RuntimeError("Daily local API budget reached. Resume after midnight Pacific or adjust your verified quota.")
            if recent[0] >= rpm or recent[1] + tokens > tpm:
                raise RuntimeError("Local minute request/token budget reached. Resume after one minute; no progress was lost.")
            db.execute("INSERT INTO calls VALUES (?,?,?,?)", (model, day, now, tokens))


class Book:
    def __init__(self, path: Path, url: str):
        self.path, self.url = path, url
        self.path.mkdir(parents=True, exist_ok=True)

    def lock(self):
        return FileLock(str(self.path / "job.lock"), timeout=0)

    def read(self, name: str, default=None):
        p = self.path / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

    def write(self, name: str, value):
        atomic_json(self.path / name, value)

    def chapter_name(self, n: int):
        if n < 1:
            raise ValueError("Chapter number must be positive")
        return f"chapters/{n:06d}"

    def chapters(self):
        return sorted((self.path / "chapters").glob("*/source.json"))
