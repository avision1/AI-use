# Runbook

## Contained setup

Use the sole existing AI-use checkout. Read AGENTS.md and HANDOFF.md, inspect Git and existing jobs, then enter `windows12/`. The current local absolute path is recorded in PROJECT_STATE.md. No other checkout, worktree, host package installation, root workflow file, host disk access or host mount is needed.

```bash
# Run after entering the existing AI-use/windows12 directory.
project_path=$(pwd -P)
test "$(basename "$project_path")" = windows12 || exit 1
mkdir -p "$project_path/.work"/{home,tmp,cache,config,data,gnupg}
export HOME="$project_path/.work/home" TMPDIR="$project_path/.work/tmp"
export XDG_CACHE_HOME="$project_path/.work/cache"
export XDG_CONFIG_HOME="$project_path/.work/config"
export XDG_DATA_HOME="$project_path/.work/data"
export GNUPGHOME="$project_path/.work/gnupg"
export PYTHONDONTWRITEBYTECODE=1
```

Do not point these writable locations outside the project or through escaping symlinks. Host bootstrap currently requires x86_64 Ubuntu 24.04, Python 3.12+, curl, dpkg-deb and gpgv plus the installed Ubuntu archive keyring (read only). Other hosts need compatible project-local tools; do not install globally to satisfy this runbook.

## Prepare and build

```bash
python3 -B scripts/build-tools.py
python3 -B scripts/build-vm.py --probe
python3 -B scripts/build-vm.py --prepare
python3 -B scripts/build-vm.py
```

Tool preparation verifies Ubuntu InRelease signatures, package-index SHA256 and package SHA256, then extracts local tools. `build/tools-lock.json` records the versions actually selected; the current resolver still uses live repository metadata, so it is a build record, not yet enforced frozen input resolution. Invalid cached downloads fail validation; preserve them for diagnosis before deliberate replacement.

The builder cloud qcow2 is pinned by build/builder-image.lock.json to dated build20261021-2638, exact image SHA512 and immutable manifest SHA256; the wrapper enforces this lock and reuses a cached legacy filename only after digest verification. Detached cloud-image signatures remain a hardening task. No claim of a fully independently signed release input chain is made. Preserve the immutable manifest and qcow2 together; upstream retention is outside this project.

This environment required `pc,accel=tcg,smm=off`; default SMM repeatedly stuck in the BIOS handler. The full software-emulated VM uses a24GiB virtual `.work/builder/build.qcow2`, based on the checked cloud image. Guest `/etc`, `/usr`, apt caches, package installation, mounts and live-build chroots exist only within that disk. No host filesystem is shared with the guest. Source snapshots and cloud-init data are served from an explicit localhost HTTP map; artifacts stream back through an allowlisted HTTP PUT endpoint into `artifacts/vm-build/` using atomic completed-file renames. QEMU has no host block-device attachments. A frozen source tarball and digest guard reuse. Managed-proxy HTTPS needs the public certificate from CODEX_PROXY_CERT, injected into the builder guest and installed with update-ca-certificates; TLS checking remains enabled. The fresh target chroot does not inherit builder CA state, and the current target hook removes the known transient build certificate if present. Guest network proxy configuration derives from the current tool invocation; do not reuse a previous invocation's port.

The guest executes Python overlay tests, builds the desktop `.deb` twice and compares digests, inspects the package, installs live-build inside the guest, and builds the KDE live/installer image with the desktop package included. Test failure must prevent the expensive ISO build. All these stages require actual successful logs; source code alone does not prove them complete.

## Monitor, stop and recover

Inspect `artifacts/vm-build/serial.log`, `guest-build.log`, `run.json`, `input-provenance.json` and `build.exit` if present. No `build.exit` or a nonzero value means incomplete/failure. A zero marker without the ISO is rejected. The OS image is not validated merely because the marker is zero.

Before starting another process, check recorded tool session/job and QEMU state. Do not start concurrent builds against one disk or output directory. A healthy build may be slow under TCG. Stop through the supervising process or QEMU control channel and preserve logs; never target unrelated processes. Inspect the recorded QEMU command to identify the correct process.

`--resume` is intended to reboot the same contained builder disk with a new cloud-init instance and rerun the recipe using the preserved source tarball, regardless of newer working-tree files; it is not a saved-memory CPU resume. It remains experimental and its first attempted rerun was inconclusive; do not treat it as verified recovery. Building newer source requires preserving the old disk and starting a separate deliberate build. Do not silently delete existing VM state. If a recorded job is alive, continue monitoring it instead of using `--resume`.

## Tests and packaging

Run runtime tests only inside the contained VM. The guest uses:

```bash
python3 -B -m unittest discover -s /root/windows12-checks/tests -v
python3 -B /root/windows12-checks/scripts/package-desktop.py
```

The packager refuses ordinary host execution. Its target tree is `image/`; its outputs are `artifacts/packages/` inside its guest source directory, then streamed by the guest to the project HTTP artifact endpoint. It creates a versioned Debian package without running installation scripts. Exact package determinism, dpkg inspection and target desktop-file validation must be recorded from actual runs. See docs/VALIDATION.md for boot, installer, application, update and hardware gates.

## Outputs, installation and release

Expected successful outputs under `artifacts/vm-build/`: `windows12-amd64-preview.iso`, `windows12-amd64-preview.packages`, SHA256SUMS, desktop package/checksum, provenance and complete logs. The current OS recipe uses mutable trixie repositories; a repeatable procedure is not a byte-identical ISO promise.

No physical installation is authorized or tested. Live boot and Calamares installation must first be tested against a new disposable virtual disk stored in this project, followed by reboot without the ISO. No release should be recommended before those results exist. Detailed manual steps and expected behavior are in docs/VALIDATION.md; the BIOS capture harness is `python3 -B scripts/boot-test.py artifacts/vm-build/windows12-amd64-preview.iso --timeout 300 --interval 30`. It collects evidence and stops; it does not certify boot or automate installation. See docs/BOOT_TEST.md. UEFI and installer automation remain pending.

Keep multi-gigabyte images, VM disks, package caches, temporary downloads and logs ignored. Git preserves source, documentation and locks. For durable exact reconstruction, separately preserve authenticated metadata/payloads, the original checked cloud image, source snapshot and commit, tool lock, generated ISO/package, package manifest, checksums and provenance. Do not store credentials or private documents in any of these.

## Checkpoint and synchronize main

Stage explicit `windows12/` files, inspect **all** staged paths and diff, and reject unrelated changes. Root README/LICENSE are intentionally unmaterialized in this checkout; their apparent deletions must never be staged. User requests frequent checkpoints directly to main.

Native push currently lacks credentials; use the authenticated GitHub connection. `python3 -B scripts/export-staged-tree.py` exports staged project text entries and rejects unrelated paths, binary payloads and symlinks. Create a tree based on the current remote tree, create a commit with current remote main as parent, then update main with expected old SHA and `force=false`. Verify returned success and fetch the remote commit. Reconcile the local main/index to the equivalent published checkpoint while preserving uncommitted files. Never overwrite unrelated history or force-push. Update memory with the previous verified checkpoint; a commit cannot embed its own SHA.

## Additional validation tools

`python3 -B scripts/build-tools.py --profile iso` prepares signature/hash-authenticated xorriso and dependencies in a separate iso-tools tree; it never replaces active QEMU files. After a real ISO exists and the main builder has stopped, `python3 -B scripts/install-test.py artifacts/vm-build/windows12-amd64-preview.iso` is the source-only D-I automation path. It holds the builder lock, refuses live legacy QMP controls, requires free space, creates a new disposable disk and demands an installer callback plus an ISO-free installed-root proof. It is not yet executed or certified. See docs/INSTALL_TEST.md. Never run source-build and install-test guests concurrently on this filesystem.

The separate two-phase recovery probe succeeded on the same disk/payload with refreshed environment; evidence and exact commands are in docs/RECOVERY.md. Both probe jobs are stopped. This proves cloud-init task rerun, not live-build partial-stage reconciliation. Keep nocloud-net unchanged across this measured path; migrating the deprecated datasource identifier needs separate validation. Do not repeat the completed probe unless changes justify it.

## Live-disk synchronization resource issue

Observed workspace synchronization created recursive temporary copies named .build.qcow2.* while the VM wrote its real disk; parallel/rapid tool executions appeared to amplify accumulation. The platform internals were not independently established. A reviewed cleanup removed42 stale regular copies and reclaimed~10.46GiB without touching configured disks/backing/source/logs.

Use a persistent `python3 -B scripts/build-monitor.py --interval 60` session and poll that existing session no more often than once per minute. The currently recorded session is in HANDOFF.md. It reports free bytes, real disk allocation, temporary-copy allocation and recent serial lines. Type status for an immediate snapshot, cleanup to apply the separate audited cleanup, or stop to stop only the monitor. Prefer this to repeated/parallel new exec invocations while large disk files change.

`python3 -B scripts/build-clean-sync.py` audits by default; `--apply` removes only regular files with the exact generated prefix beneath .work/builder, older120s, unchanged on a second stat and not an inode of the configured disk/backing. Symlinks/directories are skipped. Every removal is recorded in project-local sync-temp-cleanup.jsonl. Never replace this command with broad rm/globs or delete an active real VM disk. If copies grow unbounded despite mitigation, record the environment blocker and preserve the real build state.

Monitor handles are agent-scoped: only /root/builder can poll current68522. Root received Unknown process id for prior99317; this does not establish that the process stopped. Owner stopped99317 and replaced it with TTY-backed68522 so stdin cleanup commands work. Two reviewed cleanup passes reclaimed~10GiB each; real VM50357 remains active. Latest observed target Qt/KDE downloads~package244, real disk~1.85GB, free~24.9GB after cleanup; continuing temporary-copy growth still requires monitoring.

## Unattended resource safeguard

Use `python3 -B scripts/build-monitor.py --interval 60 --auto-cleanup` in a TTY-backed owner tool session. It runs only the reviewed stale-copy cleanup, then pauses the MAIN guest CPUs with QMP stop if less than6GiB remains. It does not quit the VM or automatically resume. Inspect paused-state.json/pause-events.jsonl and actual QMP status; explicitly reconcile storage and use `python3 -B scripts/probe-qmp.py resume --reason 'storage reconciled'` only when safe. The monitor also accepts explicit pause-vm/resume-vm/vm-status commands. Log failures cannot prevent the stop attempt; if the filesystem is full, state persistence may fail and stdout warns. Actual QMP state is authoritative.

Automatic cleanup and serialized QMP status were exercised. Pause/resume implementation was reviewed and syntax-parsed but was not exercised on the healthy build, and no disk-filling test was performed. The safeguard is configured mitigation, not proof that the hosted environment will preserve processes or storage through teardown. Git preserves source/memory; keep ignored build outputs separately within the project or rebuild from pinned inputs if workspace data is lost.

## Execution environment unavailable

Current runtime access was lost after checkpoint b0c4be0; source is durable on GitHub main. Do not assume active jobs stopped or disks vanished. Restore/attach the original Linux execution environment first, establish project boundary, and reconcile owner/provider/QMP/log/lock/exit/artifact evidence. Agent-scoped handles may be unknown in another context while processes survive. Do not launch duplicate builders or overwrite the original disk/source.

If the old VM is confirmed stopped and frozen disk/archive exist, verify the pinned base and source digest and inspect the offline image without automatic repair before guarded --resume. Refresh proxy/CA from the new invocation; never reuse an old port or disable TLS. Graceful SIGTERM/EXIT while downloads are incomplete purges their apt cache with current cachefalse; a resource CPU pause is different from guest shutdown. Actual interrupted live-build replay has not been tested.

If workspace loss is confirmed, rebuild using the existing repository and pinned cloud input, recording that concrete reason for repeated work. Ignored caches/VM disks/ISO artifacts are not preserved by Git; target repositories remain mutable, so full output byte identity is not promised. No host installation, physical disk operation, new replacement repository, extra checkout outside project, or unrelated app deployment is an acceptable workaround. Restore a Linux shell/build environment with project-contained writable storage, preferably stable local disk with ample capacity.

## Restored workspace checkpoint (2026-10-24)
Shell access returned, but original checkout/disk/cache/artifacts were absent. Sole checkout restored from existing main at the same project path, only windows12 materialized. Original runtime jobs cannot be resumed in this workspace; rebuild from pinned inputs and preserve historical validation. Current owner handles/logs are in docs/RESTORED_BUILD.md, which supersedes historical active-session numbers above. Do not run BIOS/install capture concurrently with the builder.
