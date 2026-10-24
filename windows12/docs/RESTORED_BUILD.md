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
