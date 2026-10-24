from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import wave
from .storage import digest, atomic_json
from filelock import FileLock
from .voices import validate_voice
from .preload import MODEL_REPO, MODEL_REVISION, assets

ENGINE_VERSION = "kokoro-0.9.4-" + MODEL_REVISION + "-pcm24k-v1"


def valid_wav(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as f:
            return f.getnchannels() == 1 and f.getframerate() == 24000 and f.getsampwidth() == 2 and f.getnframes() > 0
    except (OSError, EOFError, wave.Error):
        return False


def split_text(text: str, limit: int = 450):
    """Bound inference chunks without dropping any words or punctuation."""
    words = re.findall(r"\S+\s*", text)
    current = ""
    for word in words:
        if current and len(current) + len(word) > limit:
            yield current.strip()
            current = ""
        while len(word) > limit:
            if current:
                yield current.strip()
                current = ""
            yield word[:limit]
            word = word[limit:]
        current += word
    if current.strip():
        yield current.strip()


class Kokoro:
    version = ENGINE_VERSION

    def __init__(self):
        try:
            from kokoro import KPipeline, KModel
            import soundfile
        except ImportError:
            raise RuntimeError('Install speech dependencies: pip install -e ".[speech]"; install espeak-ng first') from None
        files = assets()
        self.model = KModel(repo_id=MODEL_REPO, config=files["config.json"], model=files["kokoro-v1_0.pth"])
        self.pipeline_type, self.sf = KPipeline, soundfile
        self.pipelines = {}
        self.voice_tensors = {}

    def synthesize(self, text: str, voice: dict, path: Path):
        import numpy as np
        validate_voice(voice)
        lang = voice["parts"][0]["id"][0]
        if lang not in self.pipelines:
            self.pipelines[lang] = self.pipeline_type(lang_code=lang, repo_id=MODEL_REPO, model=self.model, device="cpu")
        pipeline = self.pipelines[lang]
        import torch
        key = digest(voice["parts"])
        if key not in self.voice_tensors:
            files = assets([p["id"] for p in voice["parts"]])
            self.voice_tensors[key] = sum(torch.load(files[f'voices/{p["id"]}.pt'], weights_only=True, map_location="cpu") * p["weight"] for p in voice["parts"])
        tensor = self.voice_tensors[key]
        chunks = []
        for _, _, audio in pipeline(text, voice=tensor, speed=voice["speed"]):
            if audio is None:
                raise RuntimeError("Kokoro returned no audio")
            chunks.append(np.asarray(audio))
        if not chunks:
            raise RuntimeError("Kokoro returned empty speech")
        samples = np.concatenate(chunks)
        if not np.isfinite(samples).all() or not np.any(samples):
            raise RuntimeError("Kokoro returned invalid or silent speech")
        self.sf.write(str(path), samples, 24000, subtype="PCM_16", format="WAV")


class Renderer:
    def __init__(self, library, engine=None, remote=None, deadline=None):
        self.library, self.engine, self.remote = library, engine, remote
        self.deadline = deadline

    def render(self, book, chapter: int, script, cast: dict):
        # All inputs that affect synthesis belong in each cache key.
        version = self.engine.version if self.engine else ENGINE_VERSION
        base = book.path / book.chapter_name(chapter)
        pronunciation = book.read("pronunciation.json", {})
        plan = []
        for i, segment in enumerate(script.segments):
            text = segment.text
            for word, spoken in sorted(pronunciation.items(), key=lambda x: -len(x[0])):
                text = re.sub(r"(?<!\w)" + re.escape(word) + r"(?!\w)", lambda _: spoken, text)
            voice = cast[segment.speaker]["voice"]
            validate_voice(voice)
            for j, chunk in enumerate(split_text(text)):
                key = digest({"engine": version, "text": chunk, "voice": voice})
                plan.append({"key": key, "text": chunk, "voice": voice, "segment": i, "chunk": j,
                             "pause_ms": 0})
            plan[-1]["pause_ms"] = segment.pause_ms
        build = digest({"plan": plan, "assembly": "pcm24k-pauses-v1"})
        out = base / f"audio-{build}.wav"
        manifest_path = base / f"audio-{build}.json"
        if valid_wav(out) and manifest_path.exists():
            book.write(book.chapter_name(chapter) + "/audio.json", json.loads(manifest_path.read_text()))
            return out
        cache = self.library.root / "audio-cache"
        cache.mkdir(exist_ok=True)
        timeline, offset = [], 0.
        tmp = out.with_suffix(".tmp")
        try:
            with wave.open(str(tmp), "wb") as combined:
                combined.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                for item in plan:
                    import time
                    if self.deadline and time.monotonic() > self.deadline:
                        raise RuntimeError("Chapter generation paused at its time budget. Resume to reuse saved segments.")
                    path = cache / f'{item["key"]}.wav'
                    with FileLock(str(path) + ".lock", timeout=300):
                        if not valid_wav(path) and self.remote:
                            self.remote.get_audio(item["key"], path)
                        if not valid_wav(path):
                            if self.engine is None:
                                self.engine = Kokoro()
                            temp = path.with_suffix(".tmp")
                            try:
                                self.engine.synthesize(item["text"], item["voice"], temp)
                                if not valid_wav(temp):
                                    raise RuntimeError("Generated audio failed PCM validation")
                                os.replace(temp, path)
                                if self.remote:
                                    self.remote.put_audio(item["key"], path)
                            finally:
                                temp.unlink(missing_ok=True)
                    with wave.open(str(path), "rb") as audio:
                        duration = audio.getnframes() / 24000
                        combined.writeframes(audio.readframes(audio.getnframes()))
                    timeline.append({"segment": item["segment"], "start": offset, "end": offset+duration})
                    combined.writeframes(b"\x00\x00" * (24 * item["pause_ms"]))
                    offset += duration + item["pause_ms"]/1000
            os.replace(tmp, out)
        finally:
            tmp.unlink(missing_ok=True)
        manifest = {"build": build, "file": out.name, "engine": version, "duration_seconds": offset, "timeline": timeline}
        atomic_json(manifest_path, manifest)
        book.write(book.chapter_name(chapter) + "/audio.json", manifest)
        return out


def export_mp3(path: Path) -> Path:
    """Optional compact playback copy, always reuse the lossless master."""
    target = path.with_suffix(".mp3")
    if not target.exists():
        tmp = target.with_suffix(".tmp.mp3")
        try:
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path), "-codec:a", "libmp3lame", "-b:a", "96k", str(tmp)], check=True)
            os.replace(tmp, target)
        finally:
            tmp.unlink(missing_ok=True)
    return target
