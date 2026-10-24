# Project state

## Current milestone
M1: produce and validate a Debian13 amd64 KDE live/installer ISO with project desktop package. Source build is running; **no target ISO or installation is verified yet**.

Repository: avision1/AI-use, branch main. Previous verified synchronized checkpoint: e916574e78b74e735af2466d410013feb236a532. User requires frequent direct-to-main pushes, only windows12 changes. Native push lacks credentials; authenticated GitHub tree/commit/ref API works. Initial-to-64bff6f comparison confirmed zero changed paths outside windows12.
Absolute project: /workspace/scratch/3c38ab731138/AI-use/windows12. Parent README/LICENSE are tracked upstream but intentionally unmaterialized here; never stage their apparent deletions.

## Implemented and validated
- Persistent memory, primary-source architecture and compatibility evidence.
- image/: Office web allowlist launcher, offline welcome, eight menu entries, new-user KDE defaults, bottom panel/pins and original SVG wallpaper. GUI remains unverified.
- Contained full QEMU TCG builder, smm=off, no host filesystem shares or devices. Source snapshots served read-only via explicit HTTP map; artifact PUT exports are allowlisted, length/path checked and atomically renamed.
- Authenticated local QEMU packages and separate xorriso tools; tools are extracted, never host-installed. Immutable cloud image lock is enforced; detached cloud signature is not verified.
- Actual Debian guest Linux/systemd/cloud-init boot; guest HTTPS trust repaired using public infrastructure CA in builder only, TLS verification enabled.
- 17 overlay unit tests passed inside guest; browser invocations mocked. Desktop package built twice identically; dpkg-deb info/contents parsed successfully. Exported7036-byte package at artifacts/vm-build/windows12-desktop_0.1.0~preview1_all.deb, SHA256 eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f; host checksum matched.
- lb config succeeded; lb build entered debootstrap, verified Debian Release signature and is retrieving/validating base packages.

## Active jobs — inspect before restarting
Main build tool session50357, .work/builder/vm-launch-06.log, artifacts/vm-build/serial.log. Disk .work/builder/build.qcow2 (24GiB virtual, sparse); source SHA256 410ef567dcb06bc49f6e7e50a87f8173e0e5b3acded7b0275d3c6e68abc10ad9 in checks.tar/build-source.sha256. Latest observed stage: debootstrap completed; actual target desktop transaction queued2155MB downloads and7419MB additional installed software, including windows12-desktop. No failure marker for current run. Early package/log/checksum HTTP exports succeeded. Old diagnostic jobs are stopped and logs/disks preserved.
Recovery probe phases1 and2 are completed and stopped (sessions35102,34341). Same guest disk/payload reran with counter1→2 and refreshed proxy environment; callbacks201 and QEMU exit0. Evidence in artifacts/recovery-probe/phase-{1,2}/result.json and docs/RECOVERY.md. No probe VM is running. Main build remains the only active VM.

## Limitations and incomplete work
No ISO, target desktop, installer, installed reboot, authenticated Office, Wine/game or physical hardware tests. BIOS capture harness is implemented but unexecuted; D-I installation harness is implemented but unexecuted. Target package repositories are mutable, so full ISO byte reproducibility is not established. --resume remains experimental for live-build stages. A separate measured two-boot probe now proves frozen-payload metadata/environment rerun on the same disk using unchanged nocloud-net. Interrupted live-build stage recovery still needs verification. Namespace/Landlock isolation is unavailable; all runtime build/test work must use contained VM. No /dev/kvm, use TCG. Initial host free~30GiB; latest~28GiB. Proxy ports change per tool invocation, never hardcode.

## Exact next actions
1. Query `python3 -B scripts/probe-qmp.py status` and inspect serial.log/session50357. Continue healthy current job; do not relaunch or overwrite its controls/source/disk.
2. Monitor debootstrap, chroot package install, package validation and ISO stages. Fix only actual failures; preserve failed logs and state.
3. If ISO succeeds, verify output checksum then run BIOS capture harness, inspect screenshots and execute disposable-disk install/reboot checks. No physical installation.
4. Recovery and installation harness source has been reviewed and statically parsed. Do not rerun completed recovery probe without a reason. Execute installation harness only after ISO completion and free-space check; record exact scope/results. Update memory and push reviewed windows12-only checkpoints to main.

Source review: all11 Python source files parse via read-only AST inspection; this does not execute or validate the unrun ISO/installer harnesses. Separate xorriso startup verified from signature/hash-authenticated packages. No host package installation occurred.

Monitoring/resource note: persistent monitor session94738, owned by /root/builder, is active (scripts/build-monitor.py, .work/builder/monitor.log). Prefer having its owner poll this existing session at intervals≥60s instead of new/parallel exec calls; stdin status reports state, cleanup applies narrowly audited stale-copy removal, stop stops only monitor. Observed recursive generated .build.qcow2.* copies consumed~10.46GiB;42 stale regular copies were removed after age/inode/re-stat checks, real disk/backing preserved. Audit .work/builder/sync-temp-cleanup.jsonl. Platform synchronization is the suspected cause, not independently established. Preserve recent copies; never delete configured .qcow2 files with this cleanup.

Monitor handles are agent-scoped: only /root/builder can poll current94738. Root received Unknown process id for prior99317; this does not establish that the process stopped. Owner stopped99317 and replaced it with automatic TTY-backed94738 so stdin cleanup commands work. Two reviewed cleanup passes reclaimed~10GiB each; real VM50357 remains active. Latest observed target Qt/KDE downloads~package244, real disk~1.85GB, free~24.9GB after cleanup; continuing temporary-copy growth still requires monitoring.

Current safeguard: /root/builder owns monitor94738, build-monitor.py --auto-cleanup in a TTY-backed session. All older monitors are stopped. Reviewed stale-copy cleanup runs every60s; recent cycles kept~25–26GB free with actualdisk~2GB and desktop download~package568. If free remains below6GiB, monitor requests QMP stop of guest CPUs only, records paused-state/reason when possible and NEVER automatically resumes or quits guest. Cleanup/status were exercised; real guest pause/resume and disk-filling failure tests were not performed. Log-write failures are nonfatal, malformed marker tolerated, state markers replaced atomically where space permits. Read .work/builder/monitor.log, paused-state.json and pause-events.jsonl before action; actual QMP state overrides stale/missing markers.

Local Git may lag published checkpoints while the VM is active: native fetch/reconciliation is deferred to reduce large-file synchronization. Some staged content may already be on GitHub main. Compare remote commit/tree before committing or discarding anything; never force-push. Source checkpoints survive workspace loss; ignored VM disks/cache/artifacts require preservation or rebuild if the transient environment is removed.

Installer harness source now also requires run-specific configuration evidence: no known transient build CA/proxy artifacts, graphical.target default and SDDM unit configuration. This is statically reviewed/source-parsed only; no installer, GUI or update runtime claim. Actual GUI flag remains false until separate evidence.
