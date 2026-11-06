# Windows12 engineering instructions
Build an actual installable Linux distribution with a cohesive Windows-style experience. Support everyday workflows, including Microsoft Office via web applications where appropriate. Never claim Windows parity or tested support without evidence.

## Absolute boundary this run
The `windows12/` directory in the sole existing `AI-use` checkout (resolve its absolute path in each environment).
Every project write, dependency, cache, temporary file, log, output and agent file must stay here. Only normal Git tracking/commit/synchronization metadata may be written in the parent `.git`. Never edit the parent README, LICENSE, instructions, sibling projects, global config, host packages, host disks, or boot settings. Image `/etc` and `/usr` are allowed only in contained image storage. No root workflow files. Use project-local HOME, TMPDIR and XDG/cache directories for subprocesses. No physical installation. Isolation must fail closed; never run image package installation against the host.

## Resume
Read HANDOFF.md, PROJECT_STATE.md, TASKS.md, DECISIONS.md, RUNBOOK.md. Inspect Git branch/log/status scoped to windows12 and recorded running jobs. Reconcile real outputs before restarting jobs. Work on the highest-priority actionable task and update all memory after meaningful progress. Agents own only assigned paths; no agent commits unless explicitly assigned. Parent integrates and reviews.

## Initial repository map
`docs/`: evidence/validation, LIVE_OBSERVABILITY.md (console recovery), DESKTOP_AUDIT.md (release gates); `scripts/`: build and validation tools; `image/`: target filesystem overlays; `tests/`: checks; `.work/`: ignored caches and temporary work; `artifacts/`: ignored generated images and logs.

## Checkpoints
Update task IDs, branch/commit, validation, blockers and exact next command. Stage only windows12 paths; inspect all staged names and diff before committing. Preserve unrelated work. Synchronize through existing repository only, without force push. No large binaries in Git. Generated artifacts need explicit checksums and build provenance; original signed inputs must be archived separately for long-term reconstruction.

## Essential commands (from windows12; environment setup in RUNBOOK)
- `python3 -B scripts/build-tools.py`: prepare authenticated local tools, no install.
- `python3 -B scripts/build-vm.py --probe`, `--prepare`, then no flag: isolated VM build.
- `python3 -B scripts/build-tools.py --profile iso`: separate authenticated xorriso/unsquashfs tool tree.
- `python3 -B scripts/audit-iso.py <real-ISO> --source-archive .work/builder/checks.tar`: content gates, frozen source lock required; not a boot test.
- `python3 -B scripts/desktop-test.py <real-ISO>` in TTY: contained interactive GUI evidence after builder stops; docs/DESKTOP_TEST.md, public test data only.
- `python3 -B scripts/probe-qmp.py status` or `blockstats`: read-only state/I/O evidence; counters do not certify build success.
- `python3 -B scripts/probe-qmp.py quit`: stop only the recorded build VM when deliberately authorized by task context.
- `python3 -B scripts/build-vm.py --resume --inspect-resume --package-stage`: read-only inventory for current approved package stage; reconcile jobs first. Bare --resume is refused to protect retained work.
- `python3 -B scripts/boot-test.py artifacts/vm-build/windows12-amd64-preview.iso`: collect BIOS evidence only after real ISO exists.
- `python3 -B scripts/export-staged-tree.py`: export reviewed staged project text for authenticated GitHub main checkpoint.
Guest test command: `python3 -B -m unittest discover -s /root/windows12-checks/tests -v`. Do not run image build/package installation/test suites against the host.

Before launching a new build, runner.lock and existing QMP controls must exclude a live previous job. Do not unlink control FIFOs, replace source snapshots or rename exit markers while a job may be alive. The current bootstrap host wrapper has a launch guard; reconcile old jobs first.

## Environment unavailable
If the selected execution environment becomes unavailable, stop runtime/file operations and checkpoint through the existing GitHub connection under windows12/. Mark all job/disk/monitor status UNKNOWN until verified after restoration. An agent-scoped unknown handle is not proof of termination. Do not create replacement repos, auxiliary checkouts, host installations or broaden the boundary to work around lost access. Reconcile original state before resume/rebuild; Git preserves source/memory, not ignored transient disks.

## Current host and runtime status
Current sole project is `/workspace/AI-use/windows12/`. User explicitly authorizes useful subagents and publishing to main by default when every changed path is under windows12. Native filtered fetch restored upstream ancestry at 9107ef1; all outside-project index entries remain sparse and no sibling contents were materialized. Use fresh remote main and nonforced synchronization, preserving unrelated advancement.

Network-enabled command execution is required for proxy/loopback sockets; preserve inherited proxy/trust. Authenticated native Debian13 VM/ISO tools and pinned cloud input are ready. The sidecar-proxy relay and explicit guest TLS/signature probe passed, along with 36 guest tests/deterministic preview4 package and shutdown. Current total filesystem 7.84 GiB cannot hold full build/installation validation; user is expanding to 40+ GiB. Fresh controller refuses below 8 GiB free before dependency access/disk creation. No full builder disk or ISO exists. Reconcile actual expanded capacity and workers before launch. Current HANDOFF supersedes older runtime/network descriptions.

The historical retained-package pipeline remains available only if its exact disk/archive/plan/nonce are recovered; they are absent here. Do not use old resume commands or replay bootstrap over retained targets. Never imply source/unit/metadata tests are an installable ISO. Original signed inputs and ignored runtime artifacts need independent preservation; Git retains source and memory only.
