# Restart brief — 2026-10-24 restored shell

Read AGENTS.md, PROJECT_STATE.md, TASKS.md, DECISIONS.md and RUNBOOK.md first. Sole project `/workspace/scratch/3c38ab731138/AI-use/windows12`; only parent Git metadata is excepted from write boundary. Remote main e6b7186 was restored after supplied workspace had no old checkout/disk/cache/artifacts. Historical VM handles50357/94738 cannot resume here; no original disk/QMP exists. Root README/LICENSE intentionally unmaterialized; never stage their apparent deletions.

Active W12-005: build_restored prepares authenticated tools and rebuilds pinned Debian13 KDE image, owns `.work`, `artifacts`, regenerated tool locks and docs/RESTORED_BUILD.md. Read that file for current jobs before starting anything. Never run simultaneous VMs or replace frozen source. Use invocation-current proxy/CA, TCG smm=off, controlled HTTP and no filesystem sharing. Monitor temporary-copy growth with reviewed auto-cleanup; never auto-resume a resource-paused guest.

Active W12-007: boot_guard completed whole-run exclusive builder lock / legacy-QMP guard to boot-test.py, preserving install-test helper loading, tests and BOOT_TEST docs. Lead integrates/pushes; agents do not commit. Eight new guard tests are included in the next fresh build snapshot and must execute inside a contained VM, not host. Reviewed syntax/diff checks pass; runtime pending. Checkpoint f91d019 verified on main.

Historical evidence:17 guest tests; deterministic7036-byte desktop package SHA256eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f; real Debian builder boot; two-phase frozen-task recovery probe. No ISO, target GUI, installation or actual interrupted live-build replay verified. Those artifacts were ignored and are absent in restored workspace.

Next: inspect current preparation/build log and owner job, continue exactly one builder; review boot lock change; checkpoint source/memory directly main. After real ISO checksum, perform contained BIOS capture and new-disk install/reboot. No host install/mount/boot changes. Do not gracefully abort package downloads: cachefalse exit purge is known.
