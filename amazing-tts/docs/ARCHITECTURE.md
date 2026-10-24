# Architecture and decisions

## Shared audiobook identity

The public catalog uses SHA-256(canonical NovelPing URL + AUDIOBOOK_EDITION). Query parameters and trailing slashes are normalized. A generated edition is a shared resource, not owned playback output per user. Users request an increasing chapter target. Listening requests only read chapter metadata and issue a short-lived signed URL to a private GCS object; they never enter the generation pipeline.

Provider/model changes do not invalidate existing work. Intentionally creating another adaptation/cast edition requires a new AUDIOBOOK_EDITION; each edition automatically uses an isolated catalog collection. Old editions remain stored in their bucket prefix. Existing generated audio is not silently replaced.

## Components

- FastAPI serves the plain HTML/CSS/JS site, catalog and player. Public cloud endpoints expose metadata; generation requires Firebase Google sign-in.
- Firestore stores shared book jobs, ready-chapter records, per-user request limits and the global model quota ledger.
- Cloud Tasks invokes a PRIVATE Cloud Run worker using OIDC. API and worker use the same image with different SERVICE_MODE values. Public service does not expose worker routes.
- The worker restores saved book state, imports the next chapter, adapts it if needed, renders uncached chunks, saves chapter audio, then schedules the next chapter.
- GCS stores private original chapters, accepted scripts, candidates, casts, WAV chunk cache, manifests and MP3 playback copies. Short-lived signed playback URLs permit HTTP range requests without proxying large audio through the API.

## State machine

queued -> running -> queued (next chapter) or complete
running -> needs_review (uncertain attribution/adaptation)
running -> paused (quota, validation, time budget, provider error)
needs_review -> queued after source-preserving human approval
paused -> queued on an explicit resume request

A Firestore transaction leases one chapter at a time for a novel. Every task carries the run ID and chapter index. Stale tasks cannot advance a different run. Cloud Tasks task names deduplicate enqueues, and redelivery after a chapter commit repairs the commit-to-enqueue gap. A lease remains longer than the worker's request deadline. Transient infrastructure failures are retried by Cloud Tasks; content/provider errors pause rather than hammering a free quota. A new request resumes the same saved artifacts. Process crashes can repeat an in-flight Gemini call if its answer was never checkpointed; exactly-once external calls are not possible without provider idempotency. Accepted scripts and uploaded audio chunks are reused.

## Quality boundaries

Exact source coverage is a hard invariant, with soft adaptation similarity and attribution checks. It is a useful guard against corruption, not a semantic proof. JSON schema validation also catches malformed/truncated responses and unsupported speaker IDs. Alias collisions stop processing for repair rather than silently switching identity. Characters never change timbre based on momentary emotion. Future story revelations do not automatically recast earlier audio.

No LLM-generated instructions execute. External responses are parsed as structured data; subprocess invocation uses fixed argument arrays. Novel URLs and next links stay on the same allowlisted host and novel. No cross-domain redirects, access-challenge solving or arbitrary URL ingestion.

## Cost controls and limitations

Start with one worker instance, concurrency one, scale-to-zero public site, daily request caps and one-chapter test targets. Queue concurrency is also one to bound request pressure. CPU Kokoro avoids hosted TTS fees; model weights are baked into the cloud image to avoid redownloading at every cold start. Output rate is not a guaranteed chapters/day figure: retries consume budget and cloud compute can dominate cost. Storage and playback transfer grow with usage.

The first implementation restores book JSON state into a temporary worker directory and uploads checkpoints. This has O(number of saved chapters) metadata transfer per chapter and is deliberately simple; a large production catalog should restore only the next source plus prior summary and persist changed JSON objects. WAV chunks are shared by content hash and fetched lazily. The UI polls job state; WebSockets are unnecessary for initial traffic. Listening progress is per browser/device, not account-synced.

Cloud infrastructure needs a real-project integration test before public launch. There is no payment system, CDN, automated copyright moderation, multilingual casting, voice cloning, per-character emotional acting, or automatic quota-reset scheduler in this version. New requests are limited to 3 per signed-in user/day; playback is public. Adjust sharing rules and operational controls for the intended audience before launch.

## Primary references checked during implementation

- Gemini JSON schema output: https://ai.google.dev/gemini-api/docs/generate-content/structured-output
- Gemini quota scopes and midnight-Pacific reset: https://ai.google.dev/gemini-api/docs/rate-limits
- Kokoro inference API: https://github.com/hexgrad/kokoro
- Upstream preset inventory: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Cloud Tasks HTTP deadline and OIDC: https://docs.cloud.google.com/tasks/docs/creating-http-target-tasks
- Cloud Run pricing: https://cloud.google.com/run/pricing
- Storage pricing: https://cloud.google.com/storage/pricing
