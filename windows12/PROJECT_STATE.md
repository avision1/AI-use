# Project state — 2026-11-06

## Milestone and scope
W12-005: produce and validate first installable amd64 Debian13/KDE preview. Incomplete: no ISO, live desktop, installed boot or Windows application workflow validated. Sole project `/workspace/scratch/3c38ab731138/AI-use/windows12/`; only normal parent .git metadata excepted. Existing avision1/AI-use/main, direct main pushes authorized. Root and sibling files are intentionally unmaterialized; never stage apparent outside-project deletions.

## Current execution state
Root-owned26570/solemonitor18459 active; queue44581 waiting for successful exact build before sequential audit/BIOS/new-disk install. Current nonce0d5b71a0cc4e7593e908869976adba23. Source frozenf045... unchanged. Exact4cache quarantine/preservation PASSED, signedAPT metadata reacquisition PASSED,9base/security upgrades installed. Build advanced through kernel/firmware selection to pre-package includes. No ISO/build.exit yet at latest checkpoint; monitor~60GBfree/no sync copies. HANDOFF has exact paths/commands/handles.

Fresh80287/72465 inspections established source-backed temporary os-release diversion/classification and all14builder source hashes; raw missing finding remains visible/no-reported=false. Independent source review no blocker. Original cache-failure/refusal/quarantine proofs preserved in named artifact folders. Because target packages now change, old144package/status/MD5 recovery profile must not be blindly reused after another interruption: new stopped state requires fresh inspection/review.

## Inputs and environment
Frozen .work/builder/checks.tar SHA256 f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff unchanged. Current24GiB virtual standalone build.qcow2 converted from interrupted disk and passed offline qemu-img check0; original untouched under .work/failures/interrupted-2026-11-05 with source/logs/manifest (60 leaked clusters). No host mounts/packages/boot changes. Software TCG,2CPU4GB VM, no KVM. Native Debian13 project-local authenticated QEMU/tools available; ~60GB free at checkpoint. Dynamic proxy/CA renewed per invocation, TLS/signatures enabled. Cloud bytes pinned; cloud detached signature unavailable, assurance limits documented.

## Implemented and measured
- Windows-style Plasma first-profile setup, bottom panel, wallpaper, Office web launchers, offline help and Debian package implemented in frozen preview2 source. Actual25 guest tests passed repeatedly; desktop package rebuilt twice identically and dpkg-inspected/exported. Package7118bytes SHA2565db8cb011056994620abdfe550a31cbebc492e5a66ce2006551861484adf1776.
- Native bootstrap91 authenticated extracted tool packages; real TCG startup/cloud boot; read-only nonce-bound builder inventory; stale-lock guard and resumed public chroot measured. No full staged ISO success.
- ISO audit, BIOS capture, disposable D-I install, live desktop QA and sequential validation tools implemented/reviewed. Queue waiting/cancellation operationally passed; actual ISO gates pending. Installed desktop helper and fast unit-VM runner previously lost uncommitted work (W12-022/023), incomplete.
- Four real pinned Windows installer fixtures downloaded/hashed; Notepad++ signature and negative/offline checks passed. No Windows runtime/application executed. Native current Office unsupported; web partial; LibreOffice alternative. Hardware/UEFI/authenticated Office untested.

## Current source and ownership
Latest verified project checkpoint31a7575462d066bbad159bf95b9c48d5b671282b on main, preserving concurrent Binary School commits. Local aligned using exact windows12 tree equality. W12-030 actual cache recovery/signed refresh passed. Lead owns source/VM/Git/memory; no active source agent. Independent guard review recorded in docs/DIVERSION_GUARD_REVIEW.md. See TASKS and HANDOFF for exact next commands. GitHub API nonforced FF update works without optional expected_sha; native push lacks credentials. Never force or change unrelated history/settings.

## Next actions and release gates
Continue current26570/18459, require actual build.exit0/nonemptyISO/hostSHA/logs. Let waiting44581 run content audit, BIOS capture and new-disk D-I proof sequentially. Then review screenshots/live GUI, Calamares and installed desktop workflows. No capture-only or running-build release claim. Preserve evidence/checkpoint after meaningful progress. No physical deployment.

Git preserves source/memory, not ignored multi-GB disks/outputs. Preserve authenticated inputs/frozen source/package/logs/generated ISO separately for durable exact reconstruction; mutable Debian inputs mean no bit-identical ISO claim. Historical interruption details: docs/INTERRUPTION_2026-11-05.md and LIVE_BUILD_LOCK_RECOVERY.md; previous snapshots remain Git history.
