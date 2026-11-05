# Restart brief — Debian host recovery, 2026-11-05

Sole project: /workspace/scratch/3c38ab731138/AI-use/windows12/. Existing repository avision1/AI-use, direct main checkpoints authorized. Preserve all root/sibling files and history; only normal .git metadata excepted. Read AGENTS, PROJECT_STATE, TASKS, DECISIONS and RUNBOOK.

Workspace maintenance removed old ignored build state. Committed source restored; no old QEMU/monitor process, disk, source archive or ISO exists here. Historical 6329/82377 are not current jobs. Remote main observed c2dad1bbcf64366047dd788c14622d8451391081; local restored HEAD5432a82, clean project before this recovery edit. Other projects were not materialized; apparent outside-project deletions must never be staged.

Current host Debian13.6 x86_64, ~60GiB free, no KVM. Original Ubuntu-only bootstrap refused correctly. scripts/build-tools.py now selects native Debian or Ubuntu archives/keyring and existing sqv or gpgv; no global installation. Operational prep job72608 writes .work/tools-prepare-2026-11-05.log, signature checks started successfully. Check its actual exit/log before rerun. No VM launched yet.

Next: finish authenticated tool prep/startup/probe, verify pinned cloud base, review/freeze source and checkpoint before starting a fresh isolated build. New build must pass guest tests/package gates then real ISO/audit/GUI/install gates. Do not silently change pinned input if unavailable. Runtime tests stay in VM. The previous uncommitted W12-022 helper/mode/tests and W12-023 runner did not survive; committed source has neither. Their old conversation reports are not deliverables.

Historical evidence:25 guest tests and deterministic7036-byte preview1 package passed in October; no surviving ISO or verified installation/GUI/Windows app support. Keep these distinct from new validation. Existing artifacts are reproducible only procedurally, mutable target repositories prevent byte identity promise.
