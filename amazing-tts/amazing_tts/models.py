from __future__ import annotations

import difflib
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Character(Strict):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    name: str = Field(min_length=1, max_length=120)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    gender: Literal["male", "female", "unknown"] = "unknown"
    age: Literal["child", "young", "adult", "elder", "unknown"] = "unknown"
    traits: list[Literal["warm", "bright", "calm", "stern", "rough", "deep", "soft"]] = Field(default_factory=list)
    evidence: str = Field(min_length=1, max_length=1000)


class Segment(Strict):
    source: str = Field(min_length=1)
    text: str = Field(min_length=1)
    speaker: str
    kind: Literal["narration", "dialogue", "thought", "system"]
    confidence: float = Field(ge=0, le=1)
    emotion: Literal["neutral", "happy", "sad", "angry", "afraid", "excited", "whisper"] = "neutral"
    pause_ms: int = Field(default=220, ge=0, le=2000)


class Script(Strict):
    characters: list[Character] = Field(default_factory=list, max_length=100)
    segments: list[Segment] = Field(min_length=1, max_length=2000)
    summary: str = Field(max_length=3000)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [c.id for c in self.characters]
        if len(ids) != len(set(ids)) or "narrator" in ids:
            raise ValueError("Duplicate or reserved character IDs")
        return self


def validate_script(script: Script, source: str, known: dict) -> list[str]:
    """Hard failure on lost/reordered source; softer checks require explicit review."""
    if compact("".join(s.source for s in script.segments)) != compact(source):
        raise ValueError("Source coverage failed: text was omitted, duplicated, reordered, or invented")
    ids = set(known) | {c.id for c in script.characters} | {"narrator"}
    warnings = list(script.notes)
    for i, s in enumerate(script.segments, 1):
        if s.speaker not in ids:
            raise ValueError(f"Segment {i}: unknown speaker ID {s.speaker!r}")
        if s.kind == "narration" and s.speaker != "narrator":
            raise ValueError(f"Segment {i}: narration must use narrator")
        similarity = difflib.SequenceMatcher(None, compact(s.source).lower(), compact(s.text).lower(), autojunk=False).ratio()
        if similarity < .78:
            warnings.append(f"Segment {i}: substantial adaptation; check meaning against source")
        if s.confidence < .8 or (s.kind != "narration" and s.speaker == "narrator"):
            warnings.append(f"Segment {i}: uncertain speaker attribution")
    return warnings
