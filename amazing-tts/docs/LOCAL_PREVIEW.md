# Low-compute novel test — October 24, 2026

Input: https://novelping.com/book/building-an-eternal-dynasty-the-eternal-legacy-system

The local preview is running through the supported Sites preview daemon at **http://terminal.local:4173/**. This is a temporary workspace preview, not a Google Cloud production deployment. Leave this daemon running while the user is trying the site. No Site project was registered or publicly published.

## Exactly what is available

- All **213 original chapter bodies** are cached and readable, totalling approximately **226,998 words** in the fetched snapshot.
- The complete Chapter 1 text (**1,779 words**) was analyzed in one `gpt-6-luna` subagent run with low reasoning, used as the requested substitute for Gemini. It produced a compact paragraph-index plan rather than duplicating the novel in a long model response.
- The plan compiles to a **48-segment full chapter script**, validated for exact source coverage. Adjacent short web paragraphs are joined into speech units, quote and system-panel delimiters are removed, and the 16 cultivation-realm arrows become spoken transitions.
- Main-agent review changed paragraph 68 from thought to audible dialogue. The source supports spoken self-directed remarks. All 16 realm names and their order were checked after the arrow transformation triggered the normal adaptation warning. The original agent output and review provenance remain in the ignored book data directory.
- A **49.74-second, 108-word cast audition** is saved as WAV and MP3. It consists of selected full-script segments **0, 2 and 13**: narrator, Victor and System. It is explicitly labelled an audition, not a complete chapter recording.
- Casting: narrator `am_michael`; Victor Salvatore `am_santa`; Eternal Legacy System `bf_isabella`. Voices are fixed in the book registry. The same assignment is used whenever their passages are generated.
- Re-rendering the identical audition reused the saved recording without changing its modification time. Listening invokes neither an LLM nor speech synthesis.
- **Zero Gemini API calls.** No Google Cloud resources or paid hosted speech calls.

Full-chapter speech synthesis was slower than expected in this execution environment. Bounded attempts were stopped, retaining completed chunks, and the audition reused existing narrator/Victor chunks plus one System passage. An experimental ONNX runtime was benchmarked but is not part of the shipped application. Do not report the entire chapter or all 213 chapters as audio-ready.

## Website checks

Browser verified: 213 catalog entries, search, final chapter opens from cached text, full adapted script toggle shows `subagent:gpt-6-luna:low`, MP3 duration 49.74 seconds, playback starts and advances with no media error, and pause works. The preview tab is marked as a deliverable. The read-only snapshot disables generation and approval submissions; there is no unattended heavy compute from browser actions.

## Rebuild or resume

All saved artifacts are under `data/novels/e0c66f6c20108c74c323/`, with shared chunks in `data/audio-cache/`. Runtime data, model weights, raw source and the exported snapshot are ignored by Git. The audition scope is explicit in `chapters/000001/audio.json`, `job.json`, and `test-report.json`.

```bash
# Export the saved data without scraping or inference:
.venv/bin/python scripts/build_preview.py
# In ChatGPT Work's managed environment:
sites-preview start /absolute/path/to/AI-use/amazing-tts
# For a normal local machine, serve the exported snapshot:
python -m http.server 8080 --bind 127.0.0.1 --directory preview-dist
```

The source manifest `.openai/hosting.json` declares a static preview directory only; it has no Site project ID. The actual Python API remains available through `amazing-tts serve`. Its local text endpoint caches a requested indexed chapter, while `AMAZING_TTS_PREVIEW=1` disables generation and review mutations.

To adapt another chapter using a subagent, pass its paragraph-indexed source plus the existing cast to a lightweight model, then call `amazing_tts.agent_plan.compile_plan`. Validate/approve with the normal pipeline and preserve the model/provenance label. This offline adapter is a test/import mechanism; the website cannot spawn ChatGPT subagents by itself.

A fresh clone will not contain these novel/audio/model assets. Reimport or restore the data directory before building a populated snapshot. The production persistence target remains private GCS with Firestore metadata; that deployment still needs credentials and integration tests.
