# Restart brief — active preview2 build, 2026-11-05

Read AGENTS, PROJECT_STATE, TASKS, DECISIONS and relevant RUNBOOK sections. Sole boundary `/workspace/scratch/3c38ab731138/AI-use/windows12/`; only parent normal .git metadata excepted. Existing avision1/AI-use, direct main pushes authorized. Preserve root/siblings; their files are intentionally unmaterialized and apparent deletions must never be staged.

Latest verified main **4ffccc5ba1060d5ab328e63ebf2133904109f784**, local aligned by exact whole-tree equality. GitHub optional expected_sha currently causes upstream error; normal force=false update without it succeeds. Always use latest remote parent/base tree and verify readback; never force or overwrite concurrent sibling work.

Root-owned active builder **31920**, sole TTY auto-cleanup monitor **50947**. No agent owns these handles. Source `.work/builder/checks.tar` SHA256 **f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff**, unchanged. Disk `.work/builder/build.qcow2`, logs `.work/build-2026-11-05.log`, `artifacts/vm-build/serial.log`, `.work/builder/monitor.log`. Current UART ordinary file console, not October ringbuf. Latest base-package download through systemd; free~62.95GB/no sync copies/no pause/exit/ISO. Reconcile actual jobs/files before restarting; old6329/82377 were pruned.

**Current measured gates:** real Debian guest boot;25 tests allOK; deterministic7118-byte preview2 desktop package SHA2565db8cb011056994620abdfe550a31cbebc492e5a66ce2006551861484adf1776 exported/inspected. Full ISO/boot/install/GUI remain pending. Native Debian tool prep and diskless probe passed. Prepared ISO tools; actual content audit pending.

**New host tooling:** compat-fixtures.py/lock download four actual fixed installers, hashes/sizes verified; Notepad++ publisher signature and altered-byte rejection passed; raw key reproduction/offline/missing-cache-report checks passed. No Windows execution. Independent review doc has no remaining blocker after reporting fix. One-shot install proof source/syntax ready; installed GUI/provenance helper and fast unit VM runner lost uncommitted in previous pruning and remain pending.

**Next concrete action:** continue existing31920/50947 until actual result. Do not replace source/disk or start another VM. Require build.exit0/nonemptyISO/SHA/final log/clean supervisor, then read-only audit against frozen archive, root-owned live GUI TTY, disposable D-I proof and Calamares/installed desktop tests. Follow RUNBOOK exact commands. Monitor pauses CPUs below6GiB and never auto-resumes. No host partitions/install/mount or physical device deployment.

Generated disks/downloads/artifacts are ignored and not durable in Git; source/memory is durable on main. If pruned again, record concrete loss before rebuild and preserve historical results separately from new validation. Continue engineering toward a usable distro; do not certify a running build or input verification as a completed release.
