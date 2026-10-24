# Windows12 engineering instructions
Build an actual installable Linux distribution with a cohesive Windows-style experience. Support everyday workflows, including Microsoft Office via web applications where appropriate. Never claim Windows parity or tested support without evidence.

## Absolute boundary this run
`/workspace/scratch/3c38ab731138/AI-use/windows12/`
Every project write, dependency, cache, temporary file, log, output and agent file must stay here. Only normal Git tracking/commit/synchronization metadata may be written in the parent `.git`. Never edit the parent README, LICENSE, instructions, sibling projects, global config, host packages, host disks, or boot settings. Image `/etc` and `/usr` are allowed only in contained image storage. No root workflow files. Use project-local HOME, TMPDIR and XDG/cache directories for subprocesses. No physical installation. Isolation must fail closed; never run image package installation against the host.

## Resume
Read HANDOFF.md, PROJECT_STATE.md, TASKS.md, DECISIONS.md, RUNBOOK.md. Inspect Git branch/log/status scoped to windows12 and recorded running jobs. Reconcile real outputs before restarting jobs. Work on the highest-priority actionable task and update all memory after meaningful progress. Agents own only assigned paths; no agent commits unless explicitly assigned. Parent integrates and reviews.

## Initial repository map
`docs/`: evidence and validation; `scripts/`: build and validation tools; `image/`: target filesystem overlays; `tests/`: checks; `.work/`: ignored caches and temporary work; `artifacts/`: ignored generated images and logs.

## Checkpoints
Update task IDs, branch/commit, validation, blockers and exact next command. Stage only windows12 paths; inspect all staged names and diff before committing. Preserve unrelated work. Synchronize through existing repository only, without force push. No large binaries in Git. Generated artifacts need explicit checksums and build provenance; original signed inputs must be archived separately for long-term reconstruction.
