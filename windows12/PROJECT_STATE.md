# Project state

## Current milestone
W12-005: build, boot, install and validate the first practical amd64 Debian13/KDE preview. User explicitly requests continued work toward a fleshed-out usable distribution; a running builder is not a completed deliverable. No ISO, live desktop, installed reboot or authenticated Office workflow is verified yet.

Repository avision1/AI-use, branch main. Remote main last observed c2dad1bbcf64366047dd788c14622d8451391081; local commits b5c9452/d6609e3 are not synchronized because branch writes fail. Strict absolute project `/workspace/scratch/3c38ab731138/AI-use/windows12/`. Only parent normal Git metadata is excepted. Root README/LICENSE hashes unchanged, no root AGENTS.md. Local main has project-only commits ahead of remote. Never stage apparent outside-project deletions or force-push.


## Active recovery build — 2026-11-05
Authenticated native Debian tool prep72608 exited0:91 selected packages, QEMU1:10.0.13+ds-0+deb13u1, SeaBIOS1.16.3-2; diskless TCG10-second probe passed. Pinned cloud manifest/image both verified; prep63856 exited0. Fresh build31920 is active, sole TTY monitor50947 auto-cleanup60s. Source SHA256 `f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff`. New24GiB virtual disk in .work/builder/build.qcow2, no old state overwritten. Linux kernel/init observed; new guest tests/package/ISO still pending. Logs .work/build-2026-11-05.log, artifacts/vm-build/serial.log, .work/builder/monitor.log. Free initially63.39GB/no synchronization copies.

Preview2 source changes: independently ensure tray/clock/show-desktop; Discover update guidance; explicit Flatpak backend; kde-plasma-desktop with explicit accessibility/audio/printing/power/fonts/LibreOffice integration. Version0.1.0~preview2. AST and bash syntax/diff checks pass; functional GUI unverified.

Local recovery commit b5c9452 exists, but REMOTE MAIN IS STILL c2dad1b at last read. GitHub update_ref repeatedly returns upstream GraphQL internal error; update_file also returns internal error. Native push exits128 (credentials unavailable). No successful push is claimed. Preserve local commits and retry authenticated connection; never force-push. Root and sibling files remain untouched.
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
1. Continue build31920 and sole monitor50947; check new guest test/package gates and real stage before any restart. Native Debian tool prep/startup/probe and pinned base passed.
2. Preserve frozen source/disk. Retry GitHub synchronization of local checkpoints after verifying current main; branch write connector currently fails.
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

## Current validation checkpoint
Fresh preview2 guest:25 tests in0.391s, allOK. Deterministic double package build, dpkg info/contents and HTTP export passed. Package7118bytes, SHA256 `5db8cb011056994620abdfe550a31cbebc492e5a66ce2006551861484adf1776`, artifacts/vm-build/windows12-desktop_0.1.0~preview2_all.deb. Full ISO still building (debootstrap retrieving/validating package indexes at~159s guest uptime). No new build.exit/ISO/GUI/install result.

Separate ISO tool prep17663 completed successfully; xorriso1.5.6 started with exit0; unsquashfs4.6.1 printed its version with exit1 (its version-command status; actual SquashFS read remains pending). A verification test changed signed Debian Release cleartext and sqv rejected it with exit1; evidence .work/signature-negative-check.json.

Install harness now disables proof unit, syncs a run-token completion stamp and requires a new proof_once token marker; unit skips when stamp exists. Generated late/proof shell passes sh -n; Python AST/diff checks pass. No runtime installation or subsequent GUI boot is claimed. This host-side harness update does not modify frozen build source.

## Windows QA input / synchronization checkpoint
Four real pinned7-Zip/Notepad++ installers are cached and size/SHA256-verified; Notepad++ signature verified against full pinned fingerprint, offline recheck passed, altered-byte signature check rejected. Tool scripts/compat-fixtures.py + build/compat-fixtures.lock.json, docs/COMPAT_FIXTURES.md; no Windows execution/support claim.
GitHub push blocker resolved by omitting broken optional expected_sha while retaining force=false. Main readback confirmed b5c9452a3d3c8ac4217b1b632e780936b5a1ca40. Local d6609e3/58d2233 and newer fixture work still need publishing. Use export-staged-tree --base b5c9452a3d3c8ac4217b1b632e780936b5a1ca40 and a normal non-forced update; inspect remote for concurrent sibling changes.
