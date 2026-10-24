# Checkpoint — 2026-10-24, lightweight-agent novel preview

## Scope and standing authorization

All project work stays inside `AI-use/amazing-tts/`. Preserve repository-root files and windows12/. Normal Git metadata updates are allowed. User explicitly authorized routine pushes without asking again. Shell Git has no write credentials; use the connected GitHub account for publication, verify the remote parent, preserve its base tree, and update main with an expected SHA. Align local history only after verifying identical tree contents; retain a backup ref when publication produces new commit IDs.

Read AGENTS.md, README.md, docs/LOCAL_PREVIEW.md and actual git status before continuing. The prior implementation was published to `avision1/AI-use` through commit `a29679aaf905a4303b6d83fd0bd2f106f0e86a26`; this turn adds the lightweight-agent test and preview. Inspect the actual remote for the latest commit rather than relying on old local IDs.

## Latest user request and result

User requested a super-light subagent as a Gemini substitute, minimal compute, and hosting here so they can inspect the novel **Building an Eternal Dynasty: The Eternal Legacy System**.

- One `gpt-6-luna` subagent with low reasoning analyzed all of Chapter 1, producing a compact plan keyed by paragraph indices. Its agent has completed and been closed.
- All **213 chapters** are imported as original text; the full catalog is searchable/readable.
- Chapter 1's **1,779-word full script**, 48 merged narration/dialogue/system segments, has exact source coverage validated. Main-agent review resolved paragraph 68 as dialogue and approved the faithful 16-realm arrow conversion. Provenance is stored with the book.
- A **49.74-second / 108-word three-voice cast audition** is saved and reused on replay. It uses selected Chapter 1 segments 0, 2 and 13, not the whole chapter. UI and manifest explicitly say audition/excerpts. Zero Gemini API calls.
- Full-chapter audio attempts were stopped because synthesis was slow here; completed chunks remain reusable. Do not claim complete Chapter 1 audio, whole-book audio, or a real Gemini response.
- **55 tests pass**, Python compilation and JS syntax checks pass. Browser verified all 213 entries, final-chapter text, adapted script inspection, correct audition labelling, 49.74-second audio playback and pause without media errors.

## Live local preview — keep available for the user

Supported Sites daemon is serving **http://terminal.local:4173/** from `preview-dist/`. Browser tab is marked as a deliverable. Do not stop the preview during the user's audition. This is temporary workspace hosting, not a public production Site or Google Cloud deployment.

Managed preview could not launch the project's Python interpreter. Repaired the launch configuration to use a supported static snapshot: no alternate server, network or browser bypass. The normal Python app is retained. Snapshot routes resolve to saved JSON/audio and have no model or scraping side effects. Browser generation/review controls are disabled in preview mode.

Data: `data/novels/e0c66f6c20108c74c323/`; report: `test-report.json`; cast/script/source/agent plan/provenance beside it. Shared chunks: `data/audio-cache/`. Pinned model cache downloaded in `.scratch/huggingface/`. All these runtime assets, and `preview-dist/`, are ignored by Git. Do not commit scraped text, audio, model weights or secrets. More detail and rebuild commands: docs/LOCAL_PREVIEW.md.

## New implementation changes

- Public archive endpoint imports a complete consecutive chapter catalog without scraping hundreds of pages just for titles. Original chapter bodies were then cached serially with a two-second minimum request interval.
- Offline agent-plan compiler preserves source spans, validates ranges/overlaps and normalizes visual markup; it does not pretend to be a Gemini API integration.
- Website adds every-chapter search, cached original reading, adapted-script toggle and explicit ready-audio/audition states. Source JS/CSS are separated into package assets.
- Read-only snapshot exporter builds saved book/catalog/source/script/audio files without inference. Fingerprinted JS/CSS and uncached metadata reads prevent stale preview data.
- Local preview mode prevents generation and review writes. Python local endpoints can read indexed source and saved scripts.
- Pinned Kokoro asset loader now tries local files before network and caches resolutions; loaded voice tensors are reused across utterances.

## Existing engine and cloud status

Core CLI commands: fetch, prepare, run, status, approve, serve. Gemini uses an exact configured model ID and environment key, persistent attempt quota ledger, structured output and source validation. Character identities/aliases and voice profiles persist; audio chunks include text, voice, speed, engine and pronunciation in cache keys. WAV/timelines/MP3 are saved.

Google Cloud code includes private GCS objects/signed playback URLs, Firestore jobs/leases/quota and per-user caps, private Cloud Tasks OIDC worker, Firebase authentication, Docker/Cloud Build and Terraform. **Not deployed or cloud-integration-tested.** No real Gemini key or selected Google Cloud project is configured. See docs/DEPLOYMENT.md before launch. Terraform formatting and syntax parsing passed earlier, but provider validation was blocked by the environment's Unix socket restriction.

Known production limits: whole-book JSON mirroring per cloud chapter is not incremental; no automatic daily quota resume; in-flight model requests can repeat if a process dies before response checkpointing; semantic/speaker quality still needs listening review; voice palette is finite, English-only, without reliable expressive acting; shared cast editing is not public. Preview listening position is per device/browser.

## Next actions

1. Let the user audition the temporary site and inspect original/adapted Chapter 1. Adjust voices, pacing or pronunciation based on feedback; don't regenerate the whole novel without a useful measured resource plan.
2. If they want more audio, reuse the validated full Chapter 1 script and existing chunks. Preserve the explicit audition label until full audio actually completes. Use a single bounded worker, and measure throughput first.
3. For production, obtain proper Gemini and Google Cloud credential setup and run the deployment checklist, including auth, shared-request dedup, resumability, playback range seeking and costs.
