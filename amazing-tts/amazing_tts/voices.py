from __future__ import annotations

import itertools
from .storage import digest

# English presets from upstream VOICES.md. Descriptors are casting hints, not measured attributes.
FEMALE = ["af_heart", "af_bella", "af_nicole", "af_sarah", "af_sky", "af_alloy", "af_aoede", "af_jessica", "af_kore", "af_nova", "af_river", "bf_alice", "bf_emma", "bf_isabella", "bf_lily"]
MALE = ["am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_onyx", "am_puck", "am_santa", "bm_daniel", "bm_fable", "bm_george", "bm_lewis"]
PRESETS = FEMALE + MALE + ["am_michael"]
DEEP = {"am_adam", "am_onyx", "am_santa", "bm_george"}
BRIGHT = {"af_sky", "af_bella", "am_puck", "am_liam", "bf_alice"}
SOFT = {"af_nicole", "af_sarah", "bf_isabella", "am_echo", "bm_fable"}


def validate_voice(voice: dict):
    if not voice.get("parts") or len(voice["parts"]) > 2:
        raise ValueError("Voice needs one preset or a two-preset blend")
    prefixes = set()
    for part in voice["parts"]:
        if part["id"] not in PRESETS or not .01 <= part["weight"] <= 1:
            raise ValueError("Unknown voice or invalid blend weight")
        prefixes.add(part["id"][0])
    if len(prefixes) != 1 or abs(sum(p["weight"] for p in voice["parts"]) - 1) > .001:
        raise ValueError("Blend weights must sum to one and use the same language/accent")
    if not .7 <= voice["speed"] <= 1.3:
        raise ValueError("Voice speed must be between 0.7 and 1.3")


def signature(v):
    return digest(v["parts"])


def cast(char, existing: dict):
    pool = FEMALE if char.gender == "female" else MALE if char.gender == "male" else FEMALE + MALE
    traits = set(char.traits)
    preferred = DEEP if char.age == "elder" or traits & {"deep", "rough", "stern"} else BRIGHT if char.age in {"child", "young"} or "bright" in traits else SOFT if traits & {"soft", "calm"} else set()
    pool = sorted(pool, key=lambda x: (x not in preferred, digest([char.id, x])))
    used = {signature(v["voice"]) for v in existing.values()}
    speed = .94 if char.age == "elder" else 1.04 if char.age == "child" else 1.
    for preset in pool:
        v = {"parts": [{"id": preset, "weight": 1.}], "speed": speed}
        if signature(v) not in used:
            return v
    # Finite, reproducible extra identities; never mix accents in a blend.
    for a, b in itertools.combinations(pool, 2):
        if a[0] != b[0]:
            continue
        for weight in [.35, .5, .65]:
            v = {"parts": [{"id": a, "weight": weight}, {"id": b, "weight": 1-weight}], "speed": speed}
            if signature(v) not in used:
                return v
    raise ValueError("Voice palette exhausted. Explicitly reuse a voice in the cast editor.")


def initial_cast():
    return {"narrator": {"name": "Narrator", "aliases": [], "voice": {"parts": [{"id": "am_michael", "weight": 1.}], "speed": 1.}}}


def merge_cast(script, existing):
    """Do not let the model overwrite established identities or silently merge aliases."""
    result = {k: dict(v) for k, v in existing.items()}
    owners = {}
    for cid, c in existing.items():
        for name in [c["name"], *c.get("aliases", [])]:
            owners[name.casefold().strip()] = cid
    for c in script.characters:
        for name in [c.name, *c.aliases]:
            owner = owners.get(name.casefold().strip())
            if owner is not None and owner != c.id:
                raise ValueError(f"Alias collision: {name!r} already belongs to {owner}; repair speaker IDs before retrying")
        if c.id in result and c.name.casefold().strip() not in {n.casefold().strip() for n in [result[c.id]["name"], *result[c.id].get("aliases", [])]}:
            raise ValueError(f"Identity mismatch for established character {c.id}; keep its canonical name")
        if c.id not in result:
            result[c.id] = {**c.model_dump(), "voice": cast(c, result)}
        else:
            result[c.id]["aliases"] = sorted(set(result[c.id].get("aliases", [])) | set(c.aliases))
        for name in [c.name, *c.aliases]:
            owners[name.casefold().strip()] = c.id
    return result
