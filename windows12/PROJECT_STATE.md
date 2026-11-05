# Project state — 2026-11-05

## Milestone and boundaries
Build/boot/install/validate the first practical amd64 Debian13/KDE distribution preview (W12-005). Development remains in progress: no completed ISO, live GUI, installed reboot or Windows application workflow has yet passed.

Existing repository avision1/AI-use, branch main. Latest verified remote checkpoint before this update: `4ffccc5ba1060d5ab328e63ebf2133904109f784`. Local main was aligned after exact whole-tree equality (`34c111bb3fc75c33f7f718853e24cae0b1924e96`). Sole project `/workspace/scratch/3c38ab731138/AI-use/windows12/`; only normal parent .git metadata excepted. Root LICENSE/README and sibling project trees preserved; only windows12 materialized. Never stage apparent outside-project deletions.

## Actual active jobs
Root-owned full builder **31920** and sole TTY monitor **50947**. Command: `python3 -B scripts/build-vm.py`; monitor `python3 -B scripts/build-monitor.py --interval 60 --auto-cleanup`. Fresh24GiB virtual `.work/builder/build.qcow2` uses the exact hash-pinned cloud base. Current console is ordinary serial.log, NOT ringbuf; do not reuse October console commands blindly.

Frozen source SHA256 `f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff` matches actual `.work/builder/checks.tar` and build-source.sha256. Host-side later fixture/proof/tool/doc changes do not change that input. Never overwrite source or launch/resume another VM while this builder is alive.

Latest observed: guest bootstrap retrieving/validating base packages through systemd (~785s guest uptime); ~62.95GB free, disk allocation~393MB, synchronization temporary copies0, no build.exit/ISO/failure/pause. Exact ongoing evidence is monitor.log/serial.log, not this historical sample.

Logs: `.work/build-2026-11-05.log`, `artifacts/vm-build/{run.json,input-provenance.json,serial.log,http-requests.log}`, `.work/builder/{monitor.log,sync-temp-cleanup.jsonl}`. Final authoritative log is guest-build.log after export. Monitor cleanup protects real disk/backing; auto CPU pause below6GiB, no automatic resume. Existing handles must be reconciled before restart.

## Built and tested in this run
- Native Debian13.6 x86_64 host bootstrap:91 authenticated packages, QEMU1:10.0.13+ds-0+deb13u1 and SeaBIOS1.16.3-2 extracted locally, no global install. Existing sqv/native Debian keyring verified InRelease and package hashes. A modified signed Release was rejected (exit1). Diskless TCG10-second startup probe passed; pinned cloud manifest/image verified; fresh real Linux guest booted. No KVM.
- Fresh guest:25 tests in0.391s, allOK. Overlay package built twice identically, dpkg info/contents passed, HTTP export succeeded. Actual7118-byte `artifacts/vm-build/windows12-desktop_0.1.0~preview2_all.deb`, SHA256 `5db8cb011056994620abdfe550a31cbebc492e5a66ce2006551861484adf1776`.
- Preview2 includes per-widget tray/clock/show-desktop repair and Discover update instructions. Image recipe uses Debian kde-plasma-desktop with explicit accessibility/audio/printing/power/fonts/LibreOffice integration, plus Discover Flatpak backend. New GUI behavior remains untested.
- Separate authenticated ISO tool prep17663 passed. xorriso1.5.6 version startup exit0; unsquashfs4.6.1 prints version with exit1. Actual real-ISO/SquashFS audit pending.
- Four real fixed Windows QA installers downloaded and size/SHA256 verified. Notepad++ publisher signature verified against exact full primary fingerprint; actual altered-byte signature rejected. Raw HTTPS key bytes match pin. Offline re-verification passed; missing-cache attempt failed and invalidated report before successful recovery. No Windows binary or runtime executed. See COMPAT_FIXTURES.md and independent COMPAT_FIXTURE_REVIEW.md.
- One-shot installation proof reimplemented: disable unit, durable token stamp, required token marker and stamp condition. Python AST/generated shell syntax passed, no installation runtime result. Controlled existing-disk GUI/provenance helper is still absent.

## Recovery and Git status
Workspace maintenance removed October ignored disks/caches/outputs and uncommitted W12-022/023 source. Committed source restored from existing main; no duplicate of a surviving VM was started. Old6329/82377 and old25-test/7036-byte package records in RESTORED_BUILD are historical; those local artifacts did not survive. Current candidate has distinct inputs/results above.

GitHub lease update with expected_sha caused repeat upstream GraphQL errors; native push lacks credentials. A standard non-forced fast-forward without expected_sha succeeded twice; readback confirmed main4ffccc5. Use that proven fallback, preserving latest parent/base tree; concurrent unrelated advancement must be integrated, never forced. Exporter --base includes local committed project changes and refuses outside-project differences. No extra tools/credentials needed for normal source sync now.

## Incomplete / exact next actions
1. Continue31920/50947. Preserve healthy downloads; do not shutdown just for quiet console. Reconcile QMP and storage before any explicit resource resume.
2. Require clean supervisor exit, build.exit0, nonempty ISO, final log and host SHA256 match. Preserve failure evidence before any corrected build.
3. After main VM stops, audit actual ISO against frozen archive (docs/ISO_AUDIT.md); collect BIOS/live GUI evidence using root-owned TTY desktop-test.py; test real user/files/LibreOffice/updates/browser workflows.
4. Run D-I disposable-disk install/ISO-free boot proof, then complete provenance-checked installed GUI reuse and separate Calamares GUI validation. No physical installation.
5. Implement/validate optional Bottles lane and exact x64/x86/MSI/editor/archive/save/uninstall/offline cases using prepared fixtures. Current365 native desktop remains unsupported; web launchers partial, LibreOffice alternative.
6. Snapshot target repositories/repeat build, UEFI/SecureBoot, hardware/accessibility/localization/recovery remain release gates. Byte reproducibility is not established while target repos move. No general Windows parity or universal usability claim.
7. Keep reviewed checkpoints and direct main sync frequent; update HANDOFF and task ownership before long operations/context handoff.
