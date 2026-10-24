from __future__ import annotations

import argparse
import json
from pathlib import Path
from .storage import Library, DEFAULT_DATA
from .scraper import book_url, Scraper
from .llm import Gemini
from .pipeline import process, accept_script, needs_llm
from .audio import Renderer, export_mp3
from .models import Script


def main():
    p = argparse.ArgumentParser(description="Amazing TTS: chapter-at-a-time, cached novel audiobooks")
    p.add_argument("command", choices=["fetch", "prepare", "run", "status", "approve", "serve"])
    p.add_argument("url", nargs="?")
    p.add_argument("--data", type=Path, default=DEFAULT_DATA)
    p.add_argument("--limit", type=int, default=1, help="Chapters to process this run (default 1)")
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--model")
    p.add_argument("--daily-budget", type=int, default=480)
    p.add_argument("--rpm", type=int, default=5)
    p.add_argument("--tpm", type=int, default=100000)
    p.add_argument("--script", type=Path, help="Manually corrected script JSON for approve")
    p.add_argument("--mp3", action="store_true")
    args = p.parse_args()
    if args.command == "serve":
        import os
        import uvicorn
        os.environ["AMAZING_TTS_DATA"] = str(args.data.resolve())
        uvicorn.run("amazing_tts.web:app", host="127.0.0.1", port=8080)
        return
    if not args.url:
        p.error("Novel URL required")
    library = Library(args.data)
    book = library.book(book_url(args.url))
    try:
        with book.lock():
            if args.command == "status":
                print(json.dumps({"book": book.read("book.json"), "cast": book.read("cast.json", {}), "chapters": [
                    {"number": json.loads(path.read_text())["number"], "script": (path.parent / "script.json").exists(), "audio": (path.parent / "audio.json").exists()}
                    for path in book.chapters()]}, indent=2))
                return
            if args.command == "approve":
                source = book.read(book.chapter_name(args.start) + "/source.json")
                if not source:
                    raise ValueError("Fetch chapter first")
                record = book.read(book.chapter_name(args.start) + "/script.json")
                script = Script.model_validate_json(args.script.read_text()) if args.script else Script.model_validate(record["script"])
                accept_script(book, source, script, approve=True)
                print("Approved. Run again to generate audio from the saved script.")
                return
            llm = None
            renderer = Renderer(library) if args.command == "run" else None
            for source in Scraper().download(book, args.limit, args.start):
                if args.command == "fetch":
                    print(f'Saved {source["title"]}')
                    continue
                if needs_llm(book, source["number"]) and llm is None:
                    llm = Gemini(library, args.model, args.daily_budget, args.rpm, args.tpm)
                result = process(book, source, llm, renderer)
                if result.get("audio") and args.mp3:
                    result["mp3"] = str(export_mp3(Path(result["audio"])))
                print(json.dumps(result))
                if result["state"] == "needs_review":
                    break
    except (ValueError, RuntimeError, OSError) as exc:
        p.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
