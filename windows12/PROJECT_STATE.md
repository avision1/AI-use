# Project state

## Current milestone
W12-005: build, boot, install and validate the first practical amd64 Debian13/KDE preview. User explicitly requests continued work toward a fleshed-out usable distribution; a running builder is not a completed deliverable. No ISO, live desktop, installed reboot or authenticated Office workflow is verified yet.

Repository avision1/AI-use, branch main. Latest verified checkpoint before this update: 636fb9d3a2a057d04daf1c91f7cdfbf3c7a6444e. Strict absolute project `/workspace/scratch/3c38ab731138/AI-use/windows12/`. Only parent normal Git metadata is excepted. Root README/LICENSE hashes unchanged, no root AGENTS.md. Local HEAD remains e6b7186; staged project files include already-published API checkpoints. Before native reconciliation compare current main/index and preserve changes; never stage root deletions or force-push.

## Current execution state — 2026-11-05 (supersedes older observations)
Workspace maintenance removed the previous checkout, ignored disks, caches and artifacts. The sole checkout was restored from existing GitHub main, initially 5432a82; current remote observed c2dad1bbcf64366047dd788c14622d8451391081. Other projects exist upstream and must be preserved. Only windows12 paths are materialized. Local HEAD/index are now aligned to the restored commit, unlike the historical lag described below.

No QEMU or build monitor process exists in this workspace; .work/builder has no old build disk/source/QMP controls. Old handles 6329/82377 and October progress are historical, not current jobs. No ISO or package artifact survives locally. Historical pass results below are retained records, not a new validation.

Host changed from Ubuntu 24.04 to Debian 13.6 x86_64, ~60GiB initially available; no KVM. Existing bootstrap correctly refused it. Lead is implementing Debian archive/keyring support with existing sqv (gpgv absent). Operational prep job72608, log .work/tools-prepare-2026-11-05.log; signed trixie and updates verification succeeded so far, package extraction/startup pending. All writable state remains contained. No VM has been launched.

Uncommitted W12-022 installed-GUI/provenance changes and W12-023 check-VM runner described in the conversation did not survive and are absent from main. Their implementation and tests must be recovered or rebuilt, never claimed available. Existing committed live GUI/install harnesses remain intact.

## Implemented and measured
- Curated Office web entries/allowlisted launchers, offline help, desktop entries, KDE/Breeze/double-click defaults, first-profile bottom panel/pins and original SVG wallpaper. GUI behavior remains unverified.
- Authenticated project-local QEMU/ISO tool extraction without global installation. Full TCG builder boots Debian/systemd/cloud-init; no host shares/mounts/block devices. Current tools/base restored after previous workspace loss.
- All25 tests passed in corrected guest (17 overlay +8 boot-runner guard cases). First restored attempt had one fixture error; disk/archive/logs were preserved before corrected run.
- Desktop package built twice identically, dpkg inspected and exported:7036bytes, SHA256eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f. Available at artifacts/vm-build/windows12-desktop_0.1.0~preview1_all.deb.
- Two actual read-only blockstats snapshots73.96s apart: same virtio0 writes+16,220,160bytes/+867operations/+678flushes, reads unchanged, failed I/O0. This proved activity, not stage success. UART recovery then established actual stage from fresh text.
- Combined monitor's optional ring reader executed against existing guest with successful decode/append and cleanup. It never redirects automatically. No pause/resume or full-disk branch test claimed.
- Historical independent two-boot recovery probe passed on same disk/payload with refreshed environment; stopped before workspace outage. Actual interrupted live-build replay is still unverified.

## Incomplete work and limits
Target package repositories remain mutable; full ISO byte reproducibility and detached cloud-image signature verification pending. BIOS capture and D-I install/reboot harnesses are implemented but unexecuted. Calamares, installed desktop/admin/update/file workflows, Wine/gaming, authenticated Office, UEFI/SecureBoot and physical hardware tests remain pending; no Windows parity claim.

Source desktop audit completed in docs/DESKTOP_AUDIT.md: conditional partial-panel repair gap, update guidance precision, unassured Flatpak GUI catalog/backend, English-only project help. No source-proven boot/login blocker; real GUI tests decide fixes. Conditional chunked-storage research is unimplemented and should only be prototyped if synchronization blocks this build; never switch an active disk live.

## Exact next actions
1. Complete authenticated Debian host tool prep; require actual QEMU/qemu-img startup and diskless probe. Preserve failures. Update tool lock and checkpoint main.
2. Restore the exact pinned cloud input; inspect failures without replacing its lock silently. Before a fresh full VM, review/freeze source and record a new archive hash. Do not use --resume with a missing disk.
3. Run tests and deterministic packaging inside the new contained guest, then finish ISO/export/checksum gates. Continue the actual job with resource monitor.
4. After builder shutdown, perform ISO content audit, BIOS/live GUI and disposable installation/reboot tests. Address measured failures and implement Windows application runtime; no release-ready claim yet.
5. Reimplement missing W12-022/023 only as needed; keep checkpoint state and direct-main pushes current. No root/sibling staging or force push.

The remaining chronological sections below describe historical October work only. They are not evidence of surviving runtime outputs or current active jobs.

## Next-gate tooling checkpoint
W12-019 audit-iso.py reviewed: checks a real ISO/checksum against frozen checks.tar+source lock, actual ISO boot structures (not boot success), authenticated xorriso/unsquashfs bytes, SquashFS dpkg state, 17 core packages, managed payloads/permissions and known transient proxy/CA paths. No mount/root extraction/guest executable. ISO profile alone adds squashfs-tools; VM tool tree unaffected. Prep69510 exited0 with signed metadata/hash validation. xorriso1.5.6 / unsquashfs4.6.1 startup and requested flags confirmed; regenerated iso-tools-lock records actual packages. Real ISO audit remains pending.

Cloud detached-signature research found the current official dated release lists no signature and conventional .sign/.gpg both404; current Debian cloud guidance uses TLS/DNSSEC recommendation and distinguishes signed legacy images. No authorized cloud signature identity was established. Keep explicit HTTPS+pin assurance, no CD-key substitution or unnecessary VM restart. See docs/CLOUD_SIGNATURE_PLAN.md; target snapshot pinning remains incomplete.

Latest owner1792825209: desktopdownloads Get785, free26.35GB,disk2.253GB,four sync copies1.19GB,noerror/exit/pause. Jobs6329/82377 unchanged. Parallel W12-020 desktop-test.py harness is being implemented, no extra VM; W12-009 runtime options research is doc-only, no current image changes. Owners/acceptance in TASKS and corresponding docs.

## Graphical and next-candidate readiness
W12-020 desktop-test.py/source reviewed: shared runner lock, new contained output, read-only ISO, optional NEW disk, fixed QMP screenshot/status/keyboard/ASCII/click commands, bounded cleanup, no host devices/shares/forwards; no GUI success inferred. No real ISO/VM execution yet. Lead will own its future TTY handle to operate screenshots directly. W12-022 is queued to permit ISO-free installed desktop QA from validated prior test-run provenance into a NEW small child overlay, preserving the stopped baseline, plus a one-shot installed proof unit. That new mode is not yet implemented or validated.

Windows runtime research docs/WINDOWS_APP_RUNTIME_PLAN.md prefers an optional maintained Bottles/Flathub GUI lane after base validation, with on-demand components. No current image/runtime/app downloads or support tests. Exact harmless fixture metadata and acceptance are recorded; no native365/driver/game parity claim. App/runtime signature/hash checks must precede execution.

Image iteration research docs/IMAGE_ITERATION_PLAN.md found binary cleaning removes installer assets but retains installer stage flags in reviewed trixie source; manifests also require explicit refresh. No iteration controller exists. Match actual guest live-build version before use, preserve baseline, and never apply host chroot or running-VM changes. Expected default compression xz has not yet been reached/measured.

Latest owner1792826291: fresh desktopGet1147, free24.75GB,disk2.568GB,six synchronization copies3.56GB after cleanup; noerror/exit/pause. Existing6329/82377 active. Continue this build; prepared test tools are not completed distro gates.
