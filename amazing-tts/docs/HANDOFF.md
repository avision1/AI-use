# Checkpoint — 2026-10-24

User intent: build a well-thought-out novel-to-audiobook system inside avision1/AI-use/amazing-tts, using free AI adaptation one chapter at a time, automatic NovelPing import, many consistent automatically cast voices, permanent reusable audio, and a shared website hosted in the cloud. Google Cloud preferred unless another host proves better value.

Implemented: Python package, strict source/script models, NovelPing book/next-link importer, Gemini REST adapter, persistent budget ledger, deterministic voice registry, Kokoro synthesis adapter, content-addressed segment cache, WAV assembly/timeline and MP3 export, CLI, FastAPI website, Firebase-authenticated cloud requests, GCS/Firestore/Cloud Tasks adapters.

Currently validating; deployment files and tests are the next step. No Google Cloud deployment exists. No Gemini key has been provided. Do not claim a live fully generated sample without a real-key test. Original novel excerpts and live fetch fixtures stay in ignored data/ and .scratch/, never Git.

Keep all work in this directory. Preserve windows12 and repository-root files. Commit frequently. Next session should read README.md, AGENTS.md, this file, then actual git status and tests. See docs/ARCHITECTURE.md for design and known limits.
