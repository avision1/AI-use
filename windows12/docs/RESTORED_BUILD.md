# Restored build execution — 2026-10-24

Owner: `/root/build_restored`. Strict boundary: `/workspace/scratch/3c38ab731138/AI-use/windows12/`. No host package installation, mounts, host disks or filesystem shares.

The supplied workspace initially lacked AI-use and all ignored VM disks/cache/artifacts. Parent restored the sole checkout from GitHub main e6b71866d7f172fa654640840aa3c86a53c06921. This is a deliberate fresh build after confirmed workspace loss, not continuation of historical job50357. Historical validation remains documented; ignored original artifacts were not recovered.

Authenticated Ubuntu tool preparation completed successfully in local session28372. Log `.work/builder/tools-prepare.log` records valid Ubuntu archive signatures and package extraction; no maintainer scripts were run. The regenerated `build/tools-lock.json` records selected versions.

Diskless TCG probe and pinned Debian base preparation are active under local session25123; logs `.work/builder/probe-restored.log` and `base-prepare-restored.log`. No new build disk/source archive has yet been created. Parent reviewed the boot-test guard change; next frozen snapshot must include `tests/test_boot_guard.py`, for 25 expected guest unit tests total.

Next: verify base preparation success, launch `python3 -B scripts/build-vm.py` with fresh invocation proxy, then a persistent TTY monitor with `--interval 60 --auto-cleanup`. Record handles and frozen source hash here. No ISO/boot/install success is claimed.

Pinned base preparation exited0. Diskless QEMU stayed running10s; that is no guest OS validation. Fresh main build is active under owner `/root/build_restored`, local job69749. Persistent TTY auto-cleanup monitor is job7646. Frozen source SHA256 `b809a27d22a48fdd46fceceb663898fcefcd95fb36719aa909bb53052963449e`; host wrapper SHA256 `6e13daeeb57eda54666ad350727c16a5c74cd394fa5e31cbcfa34d6c1ded35bf`. Source archive `.work/builder/checks.tar`; real disk `.work/builder/build.qcow2`; logs `.work/builder/vm-launch-restored.log` and `artifacts/vm-build/serial.log`. Latest monitor: free31272349696bytes, disk200704bytes, no synchronization copies. Linux kernel loading observed; tests not yet reached.

## First restored guest gate result

Main job69749 exited1 and QEMU shut down cleanly. Monitor7646 exited0 after observing build.exit1. Guest unit discovery executed25tests:24passed and1errored before packaging or package installation. The failing case `test_symlink_controls_and_lock_refused(name='runner.lock')` attempted to create a symlink where an earlier test subcase had already created `runner.lock`, causing FileExistsError at tests/test_boot_guard.py:106. This is a test fixture isolation error; it does not establish a guard failure. Fail-closed gating worked: no package/ISO build was attempted.

Evidence: `artifacts/vm-build/guest-build.log`, `serial.log`, `build.exit` and `run.json`; source digest remains b809a27d22a48fdd46fceceb663898fcefcd95fb36719aa909bb53052963449e. Parent notified to review/fix test. No source archive replacement or VM relaunch performed. Next: preserve this small failed guest/source/evidence, then deliberately build a new reviewed snapshot containing the fix.

Failed source/disk/control/log files preserved under `.work/failures/restored-2026-10-24-01/`, exact rename manifest there at `manifest.json`. Guest outputs preserved under `artifacts/restored-failed-2026-10-24-01/`. Verified tools and pinned cloud base remain in `.work/builder/`. No deletion or archive replacement; waiting for reviewed fixture fix before deliberately creating a new source/disk.

## Corrected build attempt

The renamed originals reappeared after synchronization between exec calls: both the live original-path and preserved failed disk hashed SHA256 `f6556be80e9878c8f69b96f8496fb9d8de689def36b6d6375813c20aa0132ea4`; both source archives hashed the original b809a27d22a48fdd46fceceb663898fcefcd95fb36719aa909bb53052963449e. A guarded duplicate-only cleanup verified byte identity and removed the reappeared originals in the same sequential invocation as the next launch. Preserved failure bytes remain; audit `.work/failures/restored-2026-10-24-01/duplicate-restoration-audit.json`. This is an observed synchronization anomaly, not a platform mechanism diagnosis.

Parent reviewed the test fixture fix. Corrected fresh build job6329 and TTY monitor19363 are active, owner `/root/build_restored`. Source SHA256 `45cd49afcd9417f2deb185410c0e9ac93c0d25ab218f534ec209696c49cde8c4`, host wrapper `6e13daeeb57eda54666ad350727c16a5c74cd394fa5e31cbcfa34d6c1ded35bf`. Linux kernel loading observed, initial free31242723328bytes/disk200704bytes/no synchronization copies. Expected25 guest tests; outcome pending. New logs `.work/builder/vm-launch-restored-02.log`, `artifacts/vm-build/serial.log`.

Corrected guest test gate PASS: all25tests passed in the real contained VM (overlay17 + boot guard8). Deterministic desktop package double-build, dpkg-deb info/contents and early HTTP export completed. Exported `windows12-desktop_0.1.0~preview1_all.deb` is7036bytes, SHA256 `eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f`. Guest is now updating package indexes; source snapshot remains45cd49afcd9417f2deb185410c0e9ac93c0d25ab218f534ec209696c49cde8c4. At monitor time1792821591 free31212277760bytes, disk30547968bytes, no synchronization copies.

## Current resumable checkpoint

Owner `/root/build_restored` can still poll persistent monitor19363; main build6329 remains supervised and no stop/quit/powerdown/pause command has been sent. At monitor time1792822372: free30726934528bytes (~28.6GiB), actual sparse disk517349376bytes allocated, no generated synchronization copies, no failure marker or resource pause. Serial output last showed debootstrap validating libnftnl11 and has been quiet238seconds, while allocation grew from448MB to517MB; this is evidence of ongoing disk writes, not proof of a hang or completed stage. The builder has passed25guest tests and deterministic package gates; full ISO still absent/unverified.

Exact continuation: owner polls existing monitor19363 (no more often than60seconds). Observe target bootstrap completion then desktop transaction. If sustained silence also stops disk growth, use a read-only serialized QMP status query before diagnosis; do not stop healthy work. Monitor auto-cleanup remains active with6GiB pause safeguard. Once real build.exit0/ISO/checksums exist and QEMU exits, verify host checksum, then notify parent before BIOS/installation test VMs. Do not launch a duplicate VM or mutate frozen source45cd49afcd9417f2deb185410c0e9ac93c0d25ab218f534ec209696c49cde8c4. Active logs/artifacts: `.work/builder/vm-launch-restored-02.log`, `artifacts/vm-build/{serial.log,guest-build.log,run.json,input-provenance.json}`, `.work/builder/monitor.log`. Failure evidence preserved separately as above.

## Read-only live I/O observation

Serialized QMP query-blockstats snapshots `.work/builder/blockstats-01.json` and `blockstats-02.json` were collected over60seconds apart. Same qdev /machine/peripheral-anon/device[1]/virtio-backend; measured deltas {"wr_bytes": 16220160, "rd_bytes": 0, "wr_operations": 867, "rd_operations": 0, "flush_operations": 678, "failed_wr_operations": 0, "failed_rd_operations": 0, "failed_flush_operations": 0}. These measure live virtual-disk activity, not completed build stages. Matching QEMU PID2513 was present; `/proc/2513/fd/*` readlinks denied13, so stale serial inode replacement remains an unconfirmed hypothesis. Diagnostic `.work/builder/serial-fd-diagnostic.json`. No pause/resume/quit/powerdown sent.

## Latest observation endpoint

Monitor19363 remains reachable at1792823307; supervisor6329 also still reports running with no stdout/error. Disk allocated1315155968bytes (~1.225GiB), free27262136320bytes (~25.39GiB),12recent synchronization copies2666278912bytes after reviewed cleanup reclaimed~1.765GB. Serial pathname is1173seconds stale; current guest stage remains UNKNOWN. Earlier actual QMP counters established ongoing writes, and allocation continues growing. No build.exit, ISO validation, resource pause or failure is reported. Do not repeat bootstrap or restart the guest for stale console output.

Continue only the existing owner jobs; next action is monitor19363 at60second intervals and await guest final log/artifact export. If owner handles become unavailable, reconcile actualQMP/lock/process state before any restart; an unknown agent-scoped handle is not termination proof. Model handoff does not require stopping VM/monitor. Current archived source stays unchanged. A proposed chunked NBD mitigation is documentation-only and has not been implemented or applied to this live guest.
