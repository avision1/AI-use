# Amazing TTS

A shared novel audiobook website and a portable Python engine. Paste a NovelPing book URL; import chapters, adapt each whole chapter with Gemini, assign persistent character voices, generate local Kokoro speech, and play cached recordings. The Google Cloud deployment shares one edition of each book across listeners.

**Status:** implementation in progress; see docs/HANDOFF.md for verified results and deployment requirements. Cloud infrastructure is supplied as code, not yet deployed.

## Run locally

Python 3.11+ and FFmpeg required. Install espeak-ng for Kokoro pronunciation fallback.

```bash
cd amazing-tts
python -m venv .venv
source .venv/bin/activate
pip install -e '.[speech,dev]'
export GEMINI_API_KEY='your-key'
export GEMINI_MODEL='exact-model-id-from-your-AI-Studio-project'
amazing-tts serve
```

Visit http://127.0.0.1:8080. Local mode is single-user and must stay bound to localhost. Cloud mode uses Firebase sign-in for generation and private Cloud Run workers. There is no API key in the browser.

`GEMINI_MODEL` is required only for new adaptation. Model availability and quotas are not assumed. The API model ID may differ from its display name. Default local budget: 480 requests/day, 5 requests/minute, 100,000 estimated input tokens/minute. Every retry is counted. Set limits to fit your actual project quota; usage by other applications is outside this ledger. Google resets daily quotas at midnight Pacific.

## CLI

```bash
# Scrape just two chapters, without any model key or speech model:
amazing-tts fetch 'https://novelping.com/book/invincible-starting-from-the-nine-dragons-technique' --limit 2
# One complete chapter per Gemini call, then generate speech:
amazing-tts run 'https://novelping.com/book/invincible-starting-from-the-nine-dragons-technique' --limit 2 --mp3
# Inspect saved state, or prepare scripts before audio:
amazing-tts status 'https://novelping.com/book/invincible-starting-from-the-nine-dragons-technique'
amazing-tts prepare 'https://novelping.com/book/invincible-starting-from-the-nine-dragons-technique' --limit 2
# After checking source and editing a JSON script, approve it:
amazing-tts approve 'https://novelping.com/book/invincible-starting-from-the-nine-dragons-technique' --start 1 --script corrected-script.json
```

Repeat `run` with the same URL to resume. `--start`/`--limit` choose the range; scripts must be prepared in order. Use `--data PATH` to choose storage. Web chapter count means “generate through chapter N,” not “add N chapters.”

## Persistent artifacts

Everything defaults to `amazing-tts/data/` (ignored by Git): original chapter text, candidate/accepted scripts, review warnings, character registry, pronunciation dictionary, content-addressed audio chunks, chapter masters, MP3 playback copies, timeline manifests, and quota ledger. Back up this directory. Cloud mode stores state and audio in a private GCS bucket and job metadata in Firestore.

Listening never calls Gemini or Kokoro. Re-running an unchanged chapter reuses saved scripts and audio. Segment cache keys include spoken text, voice blend, speed, engine identity, and pronunciation substitutions. A changed passage only regenerates affected chunks. Chapter filenames include the build hash so the old recording remains available. Cloud listeners share the same canonical URL + edition ID. Neither model aliases nor a key change silently regenerate an existing edition.

## Fidelity and cast

The model copies original source spans alongside speech text. Validation requires all source spans in order to reproduce the chapter, ignoring whitespace. This catches omissions, duplications, reordered spans and invented source. Large speech-text changes, uncertain speakers and model notes require review. These checks cannot prove perfect meaning or speaker attribution; read the flagged passages before approval.

Characters get canonical IDs, aliases and evidence-based age/gender/trait profiles. Voice assignments are locked once created. 28 English presets are available including the narrator; additional characters use deterministic same-accent blends. Blends provide variety but are not guaranteed to sound perceptually distinct, and Kokoro does not provide reliable expressive acting controls. Thoughts keep the character's voice. Unsupported emotion labels are retained for future engines rather than advertised as performed acting. The narrator handles unresolved speech until reviewed.

For pronunciation, edit `data/novels/<book-id>/pronunciation.json`, e.g. `{"Su Mo": "Soo Moh"}`. Substitutions affect speech only, not raw text. Advanced users can edit `cast.json` between jobs using the documented voice structure; regenerate chapters to apply changes to old recordings. Back up before edits. Shared cloud cast edits require a new edition or an administrator workflow; there is no unrestricted public cast editor.

## Website and hosting

See [Google Cloud deployment](docs/DEPLOYMENT.md) and [architecture](docs/ARCHITECTURE.md). The website includes a shared bookshelf, generation requests, chapter player, autoplay, speed control, device-local listening position, cast view, and script review.

Local speech generation has no per-request provider fee, but uses your hardware. Cloud hosting, storage and bandwidth are separate costs. Only import material you may process and share. Site layouts can change; access challenges are reported, not bypassed. The observed NovelPing robots.txt disallows `/book/` crawler indexing; the importer uses identified, serial, cached requests and does not claim site endorsement or permission to redistribute.

## Development

```bash
pip install -e '.[dev,cloud]'
pytest
python -m compileall -q amazing_tts
```

Project instructions: AGENTS.md. Checkpoint: docs/HANDOFF.md. All repository changes stay inside `amazing-tts/`.
