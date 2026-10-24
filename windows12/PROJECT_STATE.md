# Project state

## Restored execution — rebuild in progress
On 2026-10-24 the Linux shell returned. The supplied workspace contained no AI-use checkout, build disk, cache or artifacts. Read-only inventory found no alternative AI-use checkout in the other supplied scratch directory. The sole checkout was restored at `/workspace/scratch/3c38ab731138/AI-use` from existing GitHub main e6b71866d7f172fa654640840aa3c86a53c06921. Only windows12 files were materialized; root README/LICENSE remain untouched/unmaterialized. Remote root tree has no repository AGENTS.md and its README/LICENSE hashes match the original baseline. Historical ignored artifacts are unavailable in this workspace; no old disk/QMP/source archive exists to resume.

Branch main. All project writes remain `/workspace/scratch/3c38ab731138/AI-use/windows12/`; parent .git is the sole metadata exception. Native Git fetch works; authenticated GitHub tree/commit/ref remains the publishing route. Last verified checkpoint f91d0195a77b67a22ba8214342552f2975208439. Rebuild is justified by concrete workspace loss, not an unknown tool handle. Prior validation below remains historical evidence; it does not imply current artifacts exist.

Active assignments: build_restored owns contained tool preparation/build runtime plus docs/RESTORED_BUILD.md; boot_guard owns boot harness serialization, its tests and docs/BOOT_TEST.md. Lead owns integration, memory and main checkpoints. Neither agent may commit or write outside windows12. Authenticated QEMU tool preparation completed; pinned base preparation follows. Shared whole-run lock/legacy-QMP guard integrated for BIOS capture with eight VM-only regression tests; syntax/diff checks passed, guest execution pending. No new ISO verified. Read docs/RESTORED_BUILD.md for current owner job handles and logs.

## Implemented and actually verified
- Six persistent memory files, primary-source architecture/compatibility research and runnable contained build tooling.
- image/: curated Office web launchers, offline welcome, desktop entries, new-user KDE/Breeze/double-click defaults, bottom panel/pins and original SVG wallpaper. GUI has not been validated.
- Project-local signature/hash-authenticated QEMU and separate xorriso dependencies, extracted without host package installation.
- Real Debian builder Linux/systemd/cloud-init boot using TCG smm=off. Host namespace isolation was unavailable; all package installs/build/runtime tests ran inside the project-contained VM.
- 17 overlay unit tests passed inside the VM (browser calls mocked).
- Desktop package built twice identically, parsed by dpkg-deb and exported. 7036 bytes; SHA256 eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f. Its prior path was artifacts/vm-build/windows12-desktop_0.1.0~preview1_all.deb; present availability is UNKNOWN.
- Independent two-boot recovery probe passed on the same disk/payload: counter 1→2, refreshed runtime environment, HTTP201 callbacks and clean QEMU exits. Both probe VMs were stopped before this outage. This is not proof of interrupted live-build recovery.
- Main source build passed debootstrap and reached desktop archive downloads. Last root-confirmed owner report: archive1391, actual build disk~3.11GB, free~23.77GB, automatic stale-copy cleanup healthy; no resource pause/error reported then. This is historical, not current status.

## Historical jobs and storage — original workspace absent
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
1. Complete authenticated local tools and pinned cloud-image preparation; owner build_restored records handles/logs in docs/RESTORED_BUILD.md.
2. Launch one contained builder, run guest test/package gates, monitor with auto-cleanup safeguard; do not start another VM while it runs.
3. Integrate fail-closed boot-test lock protection; new tests need guest runtime execution after source freeze (a subsequent controlled run if needed). Do not mutate frozen archives.
4. Verify a real ISO and checksum before boot/install harness execution. Capture BIOS desktop, test new disposable disk install and ISO-free reboot/configuration audits. No physical deployment.
5. Update memory and push reviewed windows12-only changes directly main at each meaningful checkpoint.
