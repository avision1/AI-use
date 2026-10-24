# Google Cloud deployment runbook

The code is prepared for deployment. No cloud project has been selected and no resources have been created by this session. This runbook creates billable resources in your selected project. Cloud Run, Cloud Storage, Firestore, Cloud Tasks, Cloud Build and Artifact Registry have separate billing. Set budget alerts; they are notifications, not a hard spending cap. Use one or two chapters for initial validation.

## 1. Accounts and prerequisites

Install gcloud CLI, Docker (optional with Cloud Build), Terraform 1.6+, and Python 3.11+. Select a Google Cloud project with billing enabled. Create or attach Firebase to the SAME project. In Firebase Authentication enable Google sign-in, register a web app, and copy its public apiKey/authDomain. After deployment add the Cloud Run site hostname to Firebase Authentication's authorized domains. Never put the Gemini secret in Firebase web config.

Check the Gemini Developer API model ID and free-tier quota in AI Studio. The supplied default is a local ceiling of 480 calls/day with 5 RPM, not a promise of account entitlement. Set it lower if needed. The worker uses the key from Secret Manager. No paid API fallback exists, but your Google project billing configuration ultimately determines provider charges.

If this project already has a `(default)` Firestore database, import it into Terraform instead of creating another. Its location is immutable; adjust the configuration to match it. Use a dedicated project if you want isolated quota, IAM and billing.

## 2. Build the container

Run all commands from `AI-use/amazing-tts/`. Replace placeholder values:

```bash
export TTS_PROJECT='your-project-id'
export TTS_REGION='us-central1'
export TTS_IMAGE="$TTS_REGION-docker.pkg.dev/$TTS_PROJECT/amazing-tts/app:0.1.0"
gcloud auth login
gcloud auth application-default login
gcloud config set project "$TTS_PROJECT"
gcloud services enable cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com cloudtasks.googleapis.com firestore.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com identitytoolkit.googleapis.com
gcloud artifacts repositories create amazing-tts --repository-format=docker --location="$TTS_REGION"
gcloud builds submit . --config=deploy/cloudbuild.yaml --substitutions="_IMAGE=$TTS_IMAGE"
```

The image contains CPU PyTorch, Kokoro weights, all English voice presets, espeak-ng, FFmpeg, and the English NLP model. Model assets are downloaded during build and inference runs with HF_HUB_OFFLINE=1. CPU generation is intended to fit a chapter in the 30-minute task deadline; benchmark a real chapter before committing to a huge catalog. The worker pauses at its own shorter rendering budget and resumes from chunk cache if necessary.

## 3. Configure Terraform and the secret

Create ignored `deploy/production.tfvars`:

```hcl
project_id           = "your-project-id"
region               = "us-central1"
bucket_name          = "your-globally-unique-amazing-tts-audio"
image                = "us-central1-docker.pkg.dev/your-project-id/amazing-tts/app:0.1.0"
gemini_model         = "exact-api-model-id"
firebase_api_key     = "public-firebase-web-api-key"
firebase_auth_domain = "your-project-id.firebaseapp.com"
daily_budget         = "480"
edition              = "v1"
```

```bash
terraform -chdir=deploy init
# Bootstrap APIs, service identities and the empty secret first.
terraform -chdir=deploy apply -var-file=production.tfvars -target=google_secret_manager_secret.gemini
# Enter the Gemini secret via stdin, not in command history, source files or Terraform state.
read -r -s -p 'Gemini API key: ' TTS_GEMINI_KEY
printf '%s' "$TTS_GEMINI_KEY" | gcloud secrets versions add amazing-tts-gemini-key --data-file=-
unset TTS_GEMINI_KEY
terraform -chdir=deploy plan -var-file=production.tfvars -out=production.tfplan
terraform -chdir=deploy apply production.tfplan
terraform -chdir=deploy output website_url
```

Keep Terraform state secure and backed up, preferably in a separate private GCS state bucket. The repository ignores local Terraform state and variable files. Storage/Firestore use deletion protection. There is intentionally no automatic destroy or migration of other projects.

API identity needs Firestore, object access, enqueue/actAs, Firebase user lookup and permission to sign URLs. Worker identity gets secret access, Firestore, object access and enqueue/actAs. Cloud Tasks uses a separate invoker identity; the worker has NO allUsers invoker binding. Verify the default Cloud Tasks service agent exists with its standard service-agent role; older projects may require enabling that identity as documented by Google. Worker URL is stored in job metadata by the API so workers can enqueue subsequent chapters without a resource dependency cycle.

## 4. Launch checks — required before calling this production-ready

1. Add website hostname to Firebase authorized domains; sign in using Google.
2. Request one chapter of the supplied NovelPing example. Verify raw source and accepted script objects exist in GCS. If review is requested, inspect and approve it through the website.
3. Verify a real Gemini call and real Kokoro audio; listen for correct narration/dialogue separation and pronunciation. Confirm uploaded MP3 is playable and seekable.
4. Make the same request from another browser/user. It must return saved audio without another Gemini call or TTS render. Firestore quota count must stay unchanged.
5. Request the same new novel simultaneously in two browsers. Verify one lease, one chapter task, one cast registry and one published chapter record.
6. Stop a worker mid-chapter; confirm retry/resume reuses uploaded chunks. A killed request can repeat an in-flight LLM call before its first durable checkpoint; this is an explicit limitation.
7. Call worker URL without credentials: Google Cloud must reject it. Call `/internal/chapter` on public service: must return 404. Generation without a Firebase ID token: must return 401. Saved audio should remain readable through signed URLs, while bucket contents are not public.
8. Check budget limits, request caps, worker memory/time, queue retry failures and error logs. Submit 2–3 chapters before a larger batch. Validate paused/resume and review paths.

Cloud Tasks supports at-least-once delivery, not exactly-once invocation. The distributed lease and script/audio caches suppress duplicate work after checkpointing. Review is limited to the first requester or an admin Firebase custom claim. Public discovery/playback is shared; generated source and scripts are kept private behind application authorization. Do not allow public access to the bucket or Firestore client database; all browser access goes through the API.

## Operating and moving hosts

Set an appropriate bucket retention/backup policy; versioning is enabled, so old versions consume storage until explicitly cleaned. Do not apply short blanket TTL rules to chapter masters, cast or source. Maintain lifecycle policies for obsolete versions after deciding recovery requirements. MP3 at 96 kb/s uses roughly 43 MB/hour; a 100-hour book uses about 4.3 GB for playback copies plus source, lossless masters/chunks and versions. Audio delivery can exceed storage cost.

Cloud quotas pause a job and preserve progress. Request it again after the quota reset to resume. There is no automatic daily-resume scheduler in v0.1. Configure Cloud Monitoring alerts for paused jobs and task failures; do not assume the queue retries a deliberate quota pause.

If CPU generation becomes expensive, keep the catalog/storage/API here and run the portable CLI engine on an inexpensive worker host with the same cache adapters. Compare measured generation time and outbound bandwidth before migrating; no always-on GPU is required by this design. Never expose local unauthenticated mode on a public host.
