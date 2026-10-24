# Interruption handoff

**BLOCKED: execution environment unavailable. GitHub source/checkpoints are safe; VM/disk/job survival is unknown. No ISO has been verified.**

This emergency checkpoint is REMOTE-ONLY because the shell is unavailable. Local memory may still show the prior running state; read GitHub main first. Root's read-only shell probe explicitly reported no usable execution environment. Do not retry runtime tools until an environment becomes available.

Read AGENTS.md, PROJECT_STATE.md, TASKS.md, DECISIONS.md and RUNBOOK.md. Restore execution access before runtime work. Last verified remote checkpoint before this update: b0c4be08ec3791fb1a9d030772b50d6bcfc0437a. Continue using existing avision1/AI-use main, only windows12/.

Last absolute project: /workspace/scratch/3c38ab731138/AI-use/windows12. Root README/LICENSE were intentionally unmaterialized locally; never stage their apparent deletions. Native Git can lag API commits and staged content may already be published; reconcile remote tree first, never force-push or discard blindly.

Historical main job50357 and automatic TTY monitor94738 belonged to /root/builder. Handles are agent-scoped. The last confirmed build was downloading desktop archive1391 after successful bootstrap; disk~3.11GB/free~23.77GB. No failure/pause had been reported then. Do not infer current health or death from that historical report.

Preserve/reconcile .work/builder/build.qcow2, checks.tar/build-source.sha256 (archive410ef567dcb06bc49f6e7e50a87f8173e0e5b3acded7b0275d3c6e68abc10ad9), artifacts/vm-build logs/run/provenance/exit/checksum/ISO if present, and monitor/pause/cleanup records. Both independent recovery-probe VMs were already stopped.

Completed evidence:17 guest unit tests; deterministic7036-byte desktop .deb (SHA256eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f); real builder boot; real two-phase frozen-task reboot probe. Target GUI, ISO, installer and actual interrupted live-build replay remain unverified. Source-ready boot/install harnesses are not completed tests.

Important recovery constraints:
- No host installs/mounts/boot changes/physical deployment; all writable storage remains project-contained.
- No9p shares; source/outputs use allowlisted local HTTP. Keep TCG smm=off for this host.
- Managed proxy ports change; refresh runtime environment/public CA in builder only, never disable TLS or ship transient trust in target.
- Do NOT gracefully abort a surviving download: cachefalse cleanup purges archives. Planned ACPI replay test was conditional on confirmed completed package-install stage while ISO incomplete; it was NOT performed.
- Stale synchronization copies consumed space; use only audited narrow cleanup. Auto safeguard may have paused guest CPUs below6GiB. Inspect actual QMP state and markers; never auto-resume or assume log absence means stopped.
- Ignored runtime state is not in Git. If original workspace loss is confirmed, rebuild from durable source/pinned inputs and document the reason.

**Next concrete step:** restore execution access and determine whether the original job/disk/artifacts still exist. Continue a healthy job, resume only a confirmed stopped preserved disk, or rebuild only after confirmed loss. No duplicate VM or replacement repo.
