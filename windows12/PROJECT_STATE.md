# Project state

## Availability blocker
The execution environment was reported UNAVAILABLE after checkpoint b0c4be08ec3791fb1a9d030772b50d6bcfc0437a. GitHub remains accessible, so this interruption checkpoint is being saved directly to main. No filesystem, VM, disk or process state can currently be verified. Do not assume the build stopped, survived, or completed. No target ISO has been verified.

Repository: avision1/AI-use, branch main. All project changes stay under windows12/. Readback of checkpoint b0c4be0 confirmed root LICENSE/README blob hashes unchanged. Native push lacks credentials; authenticated GitHub tree/commit/ref synchronization works. Last local absolute project path: /workspace/scratch/3c38ab731138/AI-use/windows12. Local Git may lag API-published commits; staged content may already be published. Compare remote state before discarding or committing.

## Implemented and actually verified
- Six persistent memory files, primary-source architecture/compatibility research and runnable contained build tooling.
- image/: curated Office web launchers, offline welcome, desktop entries, new-user KDE/Breeze/double-click defaults, bottom panel/pins and original SVG wallpaper. GUI has not been validated.
- Project-local signature/hash-authenticated QEMU and separate xorriso dependencies, extracted without host package installation.
- Real Debian builder Linux/systemd/cloud-init boot using TCG smm=off. Host namespace isolation was unavailable; all package installs/build/runtime tests ran inside the project-contained VM.
- 17 overlay unit tests passed inside the VM (browser calls mocked).
- Desktop package built twice identically, parsed by dpkg-deb and exported. 7036 bytes; SHA256 eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f. Its prior path was artifacts/vm-build/windows12-desktop_0.1.0~preview1_all.deb; present availability is UNKNOWN.
- Independent two-boot recovery probe passed on the same disk/payload: counter 1→2, refreshed runtime environment, HTTP201 callbacks and clean QEMU exits. Both probe VMs were stopped before this outage. This is not proof of interrupted live-build recovery.
- Main source build passed debootstrap and reached desktop archive downloads. Last root-confirmed owner report: archive1391, actual build disk~3.11GB, free~23.77GB, automatic stale-copy cleanup healthy; no resource pause/error reported then. This is historical, not current status.

## Unconfirmed jobs and storage — reconcile after restoration
Last main job: tool session50357, owner /root/builder. Last monitor: owner94738, TTY, build-monitor.py --auto-cleanup. Tool handles are agent-scoped; an unknown handle does not prove process termination.
Disk: .work/builder/build.qcow2 (24GiB virtual). Frozen archive: .work/builder/checks.tar, SHA256410ef567dcb06bc49f6e7e50a87f8173e0e5b3acded7b0275d3c6e68abc10ad9; matching build-source.sha256.
Evidence: artifacts/vm-build/{serial.log,guest-build.log,run.json,input-provenance.json,build.exit if produced}; .work/builder/{vm-launch-06.log,monitor.log,paused-state.json,pause-events.jsonl,sync-temp-cleanup.jsonl}.
Original environment availability is unknown beyond the provider's UNAVAILABLE status. Ignored disks/cache/artifacts may need preservation or rebuild if the workspace was removed.

## Known constraints and incomplete work
No completed ISO, live target desktop, installation, installed reboot, authenticated Office, Wine/game, UEFI or physical hardware validation. BIOS capture and D-I installation/reboot harnesses are source-ready but unexecuted.
Cloud image is pinned by immutable URL/hash; detached cloud signature is not verified. Target repositories remain mutable; full ISO byte reproducibility is pending.
Changing VM disks generated recursive synchronization temporary copies. Narrow cleanup was verified; an automatic monitor cleans only unchanged regular .build.qcow2.* copies older120s, protecting configured inodes. It requests QMP guest-CPU stop below6GiB after cleanup, never auto-resumes/quits. Pause/resume/full-disk branches were not runtime-tested. Actual QMP status overrides stale/missing markers.
Current cachefalse live-build cleanup PURGES completed apt archives on graceful SIGTERM/EXIT. Do not gracefully abort a surviving download. Actual staged replay test was planned only after confirmed package-install completion, before ISO completion; NO shutdown/replay test was performed before the outage. Current saved LB_APT_HTTP_PROXY is empty; fresh runtime proxy is forwarded. Never hardcode old proxy ports or disable TLS.

## Exact next actions
1. Restore/attach a working Linux execution environment; prefer the original workspace. Establish the absolute windows12 boundary before any writes. Do not create a replacement repository or auxiliary checkout.
2. Locate existing repo/cache/artifacts. Ask the existing builder owner if available; reconcile provider, QMP, logs, locks and output markers. Do NOT launch a duplicate VM merely because a scoped handle is unknown.
3. If the original job is healthy, continue it. If paused, reconcile storage and explicitly resume only after actual state is known.
4. If the old job is confirmed stopped and disk/archive survive, validate pinned base and frozen archive, inspect offline image integrity without automatic repair, then use guarded --resume and verify real stage reuse/refreshed environment. Actual staged resume remains unverified.
5. If workspace/disk loss is confirmed, rebuild from existing GitHub main source and pinned input; record this concrete reason for repeating the build. Preserve prior validation records. Do not claim bit-identical full ISO reconstruction from moving repositories.
6. After real ISO output/checksum, execute BIOS capture and new disposable-disk installation/reboot/configuration audits. No physical deployment. Update memory, inspect project-only changes and push directly main.
