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
    candidate = book.read(base + "/candidate.json")
    raw = book.read(base + "/candidate-response.json")
    if candidate:
        script = Script.model_validate(candidate)
    elif raw:
        script = Script.model_validate_json(raw["response"])
    else:
        if llm is None:
            raise ValueError("No cached script; Gemini configuration is required")
        llm.capture = lambda text: book.write(base + "/candidate-response.json", {"response": text})
        script = llm.adapt(source["text"], cast, previous["script"]["summary"] if previous else "")
    # Save unaccepted responses too, so repairs don't require another paid request.
    book.write(base + "/candidate.json", script.model_dump())
    return accept_script(book, source, script, llm.model if llm else "cached-candidate")


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


def needs_llm(book, number):
    base = book.chapter_name(number)
    return not any(book.read(base + suffix) is not None for suffix in ["/script.json", "/candidate.json", "/candidate-response.json"])
