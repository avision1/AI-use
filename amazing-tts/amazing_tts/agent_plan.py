"""Compile a compact offline agent analysis into the normal validated audiobook script.

This is a test/import adapter: it makes no external requests and does not impersonate
Gemini. The selected model and its original plan are recorded separately as provenance.
"""
from __future__ import annotations

import re
from .models import Script, Segment, Character, validate_script


def spoken(text: str) -> str:
    pairs = {'"': '"', '“': '”', '[': ']'}
    text = text.strip()
    if text and pairs.get(text[0]) == text[-1]:
        text = text[1:-1].strip()
    text = text.replace('→', ', then ').replace('...', '…')
    return re.sub(r'!{2,}', '!', text).strip()


def compile_plan(source: str, plan: dict, known=None) -> Script:
    paragraphs = source.split('\n\n')
    assignments = {}
    for assignment in plan.get('assignments', []):
        start, end = assignment['start'], assignment['end']
        if not (isinstance(start, int) and isinstance(end, int) and 0 <= start <= end < len(paragraphs)):
            raise ValueError('Agent assignment is outside the chapter')
        for index in range(start, end+1):
            if index in assignments:
                raise ValueError('Overlapping agent speaker assignments')
            assignments[index] = assignment
    replacements = {}
    for replacement in plan.get('replacements', []):
        index = replacement['paragraph']
        if not isinstance(index, int) or not 0 <= index < len(paragraphs) or index in replacements:
            raise ValueError('Invalid or duplicate agent replacement')
        replacements[index] = replacement['text']
    segments = []
    for index, original in enumerate(paragraphs):
        a = assignments.get(index, {})
        segment = Segment(source=original, text=replacements.get(index, spoken(original)),
                          speaker=a.get('speaker', 'narrator'), kind=a.get('kind', 'narration'),
                          confidence=a.get('confidence', 1), emotion=a.get('emotion', 'neutral'), pause_ms=180)
        # Combine short web paragraphs: they are layout fragments, not 250 dramatic pauses.
        if segments and all(getattr(segments[-1], k) == getattr(segment, k) for k in ['speaker', 'kind', 'emotion']) and len(segments[-1].text) + len(segment.text) < 700:
            segments[-1].source += '\n\n' + original
            segments[-1].text += ' ' + segment.text
            segments[-1].confidence = min(segments[-1].confidence, segment.confidence)
        else:
            segments.append(segment)
    script = Script(characters=[Character.model_validate(c) for c in plan.get('characters', [])], segments=segments,
                    summary=plan.get('summary', ''), notes=plan.get('notes', []))
    validate_script(script, source, known or {})
    return script
