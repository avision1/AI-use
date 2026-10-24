# Project state

## Current milestone
W12-005: build, boot, install and validate the first practical amd64 Debian13/KDE preview. User explicitly requests continued work toward a fleshed-out usable distribution; a running builder is not a completed deliverable. No ISO, live desktop, installed reboot or authenticated Office workflow is verified yet.

Repository avision1/AI-use, branch main. Latest verified checkpoint before this update: 636fb9d3a2a057d04daf1c91f7cdfbf3c7a6444e. Strict absolute project `/workspace/scratch/3c38ab731138/AI-use/windows12/`. Only parent normal Git metadata is excepted. Root README/LICENSE hashes unchanged, no root AGENTS.md. Local HEAD remains e6b7186; staged project files include already-published API checkpoints. Before native reconciliation compare current main/index and preserve changes; never stage root deletions or force-push.

## Active build and supervision
Original corrected build6329 remains running, owner /root/build_restored. Frozen source SHA25645cd49afcd9417f2deb185410c0e9ac93c0d25ab218f534ec209696c49cde8c4; real disk `.work/builder/build.qcow2`. Do not launch a duplicate VM, use --resume, replace archive or convert active storage. See docs/RESTORED_BUILD.md for full provenance/failure preservation.

The original file-backed console became stale despite real block I/O. Source-reviewed QEMU UART backend recovery succeeded once at1792824075: actual serial0 changed from stdio to 1MiB ringbuf, frontend stayed open, compat_monitor0 QMP pipe unchanged, QMP runningtrue. This changed host console handling, not guest CPU/disk/boot commands. Future output only; consuming reads do not recover historical bytes. Do not reissue console-ringbuf: it would discard retained output.

Storage-only monitor19363 was stopped cleanly with its stop command; builder6329 was unaffected. New SOLE combined TTY monitor82377 is active: `python3 -B scripts/build-monitor.py --interval 60 --auto-cleanup --console-id serial0`. It runs reviewed narrow stale-copy cleanup/6GiB CPU-pause safeguard first, then bounded read-only ring reads and safe project log append. Actual initial operation:8146bytes logged across two reads, no pending data/error; next observation1815bytes. No separate watcher or second consumer exists.

Fresh console confirms bootstrap completed and desktop package downloads are active: Get483 then Get497libperl5.40 at1792824366. Latest monitor free26.52GB, disk2.121GB, seven temporary copies2.60GB after cleanup2.356GB; no build.exit/pause/ISO. Project host observer changes are outside the unchanged frozen guest input.

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
1. Continue existing6329/82377; poll owner handle, not new FS execs each minute. Inspect fresh console fields/log plus storage/exit evidence. One ring consumer only.
2. On a resource CPU pause, reconcile actual QMP/free/stale copies before explicit resume; no automatic resume. Never gracefully abort downloads: cachefalse exit purges archives.
3. Wait for real build.exit/ISO/checksums/final guest log and supervising exit; verify nonempty ISO and host SHA256. Preserve failed evidence if nonzero/missing.
4. After builder stops, inspect actual media then BIOS boot and NEW disposable-disk install/ISO-free reboot. Test graphical workflows and fix measured failures before release; no host or physical installation.
5. Maintain memory, reviewed project-only checkpoints and frequent direct main pushes.

## Next-gate tooling checkpoint
W12-019 audit-iso.py reviewed: checks a real ISO/checksum against frozen checks.tar+source lock, actual ISO boot structures (not boot success), authenticated xorriso/unsquashfs bytes, SquashFS dpkg state, 17 core packages, managed payloads/permissions and known transient proxy/CA paths. No mount/root extraction/guest executable. ISO profile alone adds squashfs-tools; VM tool tree unaffected. Prep69510 exited0 with signed metadata/hash validation. xorriso1.5.6 / unsquashfs4.6.1 startup and requested flags confirmed; regenerated iso-tools-lock records actual packages. Real ISO audit remains pending.

Cloud detached-signature research found the current official dated release lists no signature and conventional .sign/.gpg both404; current Debian cloud guidance uses TLS/DNSSEC recommendation and distinguishes signed legacy images. No authorized cloud signature identity was established. Keep explicit HTTPS+pin assurance, no CD-key substitution or unnecessary VM restart. See docs/CLOUD_SIGNATURE_PLAN.md; target snapshot pinning remains incomplete.

Latest owner1792825209: desktopdownloads Get785, free26.35GB,disk2.253GB,four sync copies1.19GB,noerror/exit/pause. Jobs6329/82377 unchanged. Parallel W12-020 desktop-test.py harness is being implemented, no extra VM; W12-009 runtime options research is doc-only, no current image changes. Owners/acceptance in TASKS and corresponding docs.

## Graphical and next-candidate readiness
W12-020 desktop-test.py/source reviewed: shared runner lock, new contained output, read-only ISO, optional NEW disk, fixed QMP screenshot/status/keyboard/ASCII/click commands, bounded cleanup, no host devices/shares/forwards; no GUI success inferred. No real ISO/VM execution yet. Lead will own its future TTY handle to operate screenshots directly. W12-022 is queued to permit ISO-free installed desktop QA from validated prior test-run provenance into a NEW small child overlay, preserving the stopped baseline, plus a one-shot installed proof unit. That new mode is not yet implemented or validated.

Windows runtime research docs/WINDOWS_APP_RUNTIME_PLAN.md prefers an optional maintained Bottles/Flathub GUI lane after base validation, with on-demand components. No current image/runtime/app downloads or support tests. Exact harmless fixture metadata and acceptance are recorded; no native365/driver/game parity claim. App/runtime signature/hash checks must precede execution.

Image iteration research docs/IMAGE_ITERATION_PLAN.md found binary cleaning removes installer assets but retains installer stage flags in reviewed trixie source; manifests also require explicit refresh. No iteration controller exists. Match actual guest live-build version before use, preserve baseline, and never apply host chroot or running-VM changes. Expected default compression xz has not yet been reached/measured.

Latest owner1792826291: fresh desktopGet1147, free24.75GB,disk2.568GB,six synchronization copies3.56GB after cleanup; noerror/exit/pause. Existing6329/82377 active. Continue this build; prepared test tools are not completed distro gates.
