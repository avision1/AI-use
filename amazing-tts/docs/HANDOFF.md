# Checkpoint — 2026-10-24

## User intent and scope

Build a novel audiobook system inside `avision1/AI-use/amazing-tts/`. Input is a NovelPing book URL; automatically import it, adapt one whole chapter per free-model request, detect/cast many characters, keep voices consistent across the novel, and save all generated speech for reuse. User then requested a shared cloud website: generate each novel once, store everything centrally, and serve existing audio to every listener. Google Cloud is the chosen initial implementation; user allows other hosts if justified by cost.

All project source, progress and test work lives in this folder. Preserve windows12/ and repository-root files. Existing MIT repository license applies. No agents were delegated in this session.

## Implemented

- Installable Python package and CLI: fetch, prepare, run, status, approve, serve.
- Allowlisted NovelPing importer, serial requests with at least 2-second spacing, cached raw chapters and consecutive next-link traversal beyond the first-30 preview. No challenge bypass or arbitrary URL fetch.
- Gemini REST structured-output adapter. Exact model ID and key come from environment. One whole-chapter response; malformed, blocked or truncated output does not generate audio. Candidate/response checkpoints avoid paying again to repair a rejected response.
- Exact source-span coverage, structured schema and speaker validation; substantial adaptations and uncertain attribution pause for review. This does not prove perfect semantics or attribution.
- Persistent canonical character/alias registry, evidence-based gender/age/trait profiles, locked casting, 28 English presets including narrator, deterministic same-accent blends for extra identities. Emotion metadata is retained but is not performed acting by Kokoro.
- Real CPU Kokoro with pinned model revision f3ff3571791e39611d31c381e3a41a3af07b4987, reusable WAV chunks, keyed text/voice/speed/engine/pronunciation cache, WAV assembly, timing manifest, MP3 playback copies, per-book/per-chunk locks.
- FastAPI responsive website: shared bookshelf, generation requests, chapter playlist/autoplay, speed, device-local listening position, cast view, source/script review, saved-audio playback. Local mode binds localhost only.
- Google Cloud adapters: private GCS state/audio objects and signed playback URLs; Firestore shared catalog, leases, quota ledger and per-user generation caps; Cloud Tasks chapter jobs with OIDC and resumable state machine; Firebase Google authentication for generation; owner/admin review authorization. Shared target extension and stale-task/commit-to-enqueue recovery are unit-tested.
- Docker/Cloud Build image configuration with preloaded model assets; Terraform resources for public API, private worker, private bucket, Firestore, queue, service accounts/IAM and Secret Manager; deployment runbook.

## Verified results

- **45 pytest tests passed**: coverage corruption, alias/identity collisions, >28 unique casts, immutable voice assignment, quota reservations, interrupted synthesis, exact audio reuse, single-chunk invalidation, source continuity, importer >30 chapters, provider truncation/429 behavior, API cached requests/auth, cloud lease/state/target/queue logic with in-memory fakes.
- Live requested NovelPing input: first two chapters imported and cached locally (1,525 and 1,532 words). No scraped novel text is committed.
- Real Kokoro inference on ORIGINAL test text, narrator plus two characters: ~10.975 seconds of valid speech, WAV and MP3 created; second render reused the same recording without changing its modification time. Initial smoke run including initialization/download checks took ~39.67 seconds. This is not a production throughput benchmark.
- All English Kokoro assets preloaded successfully. Kokoro imports with the installed CPU PyTorch and spaCy English model.
- Browser checks with headless Chromium: desktop/mobile layouts, saved novel detail, invalid URL feedback, no horizontal mobile overflow, no browser JS exceptions. Screenshots inspected. Playback test still needs a Gemini-adapted real novel chapter and cloud-hosted URL/range seek checks.
- Python compile checks and JavaScript syntax checks passed.
- Terraform init succeeded with Google provider 6.50.0; `terraform fmt -check` and independent HCL parse passed. Full provider-schema validation could not run because this environment blocks the provider's Unix socket (`socket: operation not permitted`). No Terraform apply or cloud integration test occurred.

## Credentials, deployment and publication status

No Gemini API key or Google Cloud project credentials are configured. No website is publicly hosted. Do not claim a complete real Gemini-to-cloud chapter run or a live cloud service. Cloud SDK logic is implemented and unit-tested with fakes; SDK calls, IAM, Secret Manager, Firebase sign-in and GCS delivery still need the deployment checklist in docs/DEPLOYMENT.md.

Two initial local commits were created: `de72fd4`, `8bfa2c2`; a final validation/handoff commit follows this checkpoint. All local tracked changes are under amazing-tts/. An initial `git push origin main` was rejected by automatic approval review pending explicit authorization. The user subsequently explicitly authorized pushes: “yes no need to ask pemission before push. just do not use any folder outside of your current project directory”. Routine pushes are now authorized; keep all project file changes inside amazing-tts/ and verify remote movement before publishing. The last known remote HEAD is `696bc1cf7cc21c4d42881e93aa6e85458085fa95`. Implementation and validation progress are committed locally. Publication is being completed under the user’s explicit authorization; check the actual remote before describing its status.

## Next actions

1. Push the completed local commits to main under the authorization above. Inspect remote movement before pushing; preserve other projects. Do not ask again for routine pushes within this project.
2. Get the user's selected Google Cloud project, exact Gemini model ID and key via proper credential setup. Read docs/DEPLOYMENT.md; prepare a concrete Terraform plan before resource creation.
3. Run a real chapter adaptation; inspect speaker attributions and listen to the result. Check novel-specific pronunciations and correct through persisted pronunciation.json.
4. Complete cloud launch checks: simultaneous user dedup, private worker rejection, sign-in, shared playback without Gemini quota changes, range seeking, worker interruption, quota pause/resume and cost measurement.

## Known limitations / future work

- No cloud deployment or real Gemini call has been validated. Docker image configuration has not been built in this environment.
- Cloud state mirroring transfers all saved JSON per chapter, so metadata operations grow quadratically across a long novel. Improve incremental state loading/saving before a large public catalog.
- Exactly-once external calls are not guaranteed: a crash before the first successful response checkpoint can repeat a Gemini call. Checkpointed scripts/chunks are reused. The distributed lease/worker deadline reduces overlaps but needs real crash testing.
- Quota/time-budget/provider failures pause jobs; a new explicit request resumes them. Automatic next-day scheduling is not implemented.
- Shared catalog is public playback, Firebase sign-in required for new generation, 3 generation/resume/extension requests per user per UTC day. Edition catalogs are isolated; change AUDIOBOOK_EDITION for a new edition, not silent recasting.
- Limited automated semantic validation, finite/perceptually overlapping voice palette, English only, no expressive acting/voice cloning. Global shared cast editing is intentionally not public.
- Runtime data/, .scratch/, .venv/, secret values, Terraform state and model/audio binaries are ignored. Back up persistent data and cloud state. See README.md for run commands and examples/speech_smoke.py for a repeatable real speech test without an API key.
