# Runbook
## Setup and boundary
Run from the sole existing AI-use checkout. Resolve `windows12` to an absolute path and reject symlink escapes. Put HOME, TMPDIR, XDG_CACHE_HOME, XDG_CONFIG_HOME, XDG_DATA_HOME and tool caches under `windows12/.work`. No global installs. Do not create .github workflows outside the boundary.
## Build
Build command and verified input procedure are under implementation (W12-003). No usable release image exists yet. No host installer, host mounts or privileged container fallback permitted.
## Tests
No tests run yet. Use only a contained environment with project-local writable storage.
## Install
Not yet validated. Only disposable virtual disks inside project are authorized test targets. Physical device installation is not authorized.
## Recovery and preservation
Read HANDOFF and reconcile Git/output files. No build currently running. Source/configurations are tracked. Downloaded ISOs, package payloads, caches, VM disks and generated ISOs are ignored; preserve signed base image, digest, provenance and release artifacts separately if exact reconstruction matters. Do not commit multi-GB outputs.
