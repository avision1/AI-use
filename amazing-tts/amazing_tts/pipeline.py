from __future__ import annotations

from .llm import PROMPT_VERSION
from .models import Script, validate_script
from .storage import digest
from .voices import initial_cast, merge_cast


def prepare(book, source: dict, llm):
    base = book.chapter_name(source["number"])
    saved = book.read(base + "/script.json")
    source_hash = digest(source["text"])
    if saved:
        if saved["source_hash"] != source_hash:
            raise ValueError("Source changed; create a new edition rather than overwriting the existing audiobook")
        # Saved scripts remain reusable even if model configuration changes.
        return Script.model_validate(saved["script"]), saved
    cast = book.read("cast.json", initial_cast())
    previous = book.read(book.chapter_name(source["number"]-1) + "/script.json") if source["number"] > 1 else None
    if source["number"] > 1 and previous is None:
        raise ValueError("Prepare chapters in order to preserve character continuity")
    script = llm.adapt(source["text"], cast, previous["script"]["summary"] if previous else "")
    # Save unaccepted responses too, so repairs don't require another paid request.
    book.write(base + "/candidate.json", script.model_dump())
    return accept_script(book, source, script, llm.model)


def accept_script(book, source, script, model="manual", approve=False):
    base = book.chapter_name(source["number"])
    cast = book.read("cast.json", initial_cast())
    warnings = validate_script(script, source["text"], cast)
    new_cast = merge_cast(script, cast)
    # Commit cast first: interruption leaves unused identities, never a script with missing voices.
    book.write("cast.json", new_cast)
    record = {"source_hash": digest(source["text"]), "model": model, "prompt_version": PROMPT_VERSION,
              "warnings": warnings, "approved": approve or not warnings, "script": script.model_dump()}
    book.write(base + "/script.json", record)
    return script, record


def process(book, source, llm, renderer=None):
    script, record = prepare(book, source, llm)
    if not record["approved"]:
        return {"chapter": source["number"], "state": "needs_review", "warnings": record["warnings"]}
    path = renderer.render(book, source["number"], script, book.read("cast.json")) if renderer else None
    return {"chapter": source["number"], "state": "ready" if path else "prepared", "audio": str(path) if path else None}
