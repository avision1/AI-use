# Contained live-image BIOS capture

`boot-test.py` runs project-local QEMU/SeaBIOS in software emulation (`pc,accel=tcg,smm=off`). It attaches an existing project-contained ISO read-only, uses explicit VGA with no network or host shares, and collects QMP status plus framebuffer captures. It never installs to a host disk, mounts a host filesystem, or starts an automated installation.

## Prerequisites and invocation

The capture harness holds `.work/builder/runner.lock` for the entire run, including emulator cleanup. A source-build or install-test runner holding that lock blocks capture before any output directory or guest is created. Surviving legacy builder QMP FIFO listeners and ambiguous/non-FIFO/symlink controls also block capture; inspect the recorded job instead of deleting controls. A stale, complete FIFO pair with no listener is permitted and left unchanged. Do not run independent project VMs concurrently.

The project QEMU tools must already exist under `.work/builder/tools` and an actual ISO must exist beneath `windows12`. From `AI-use/windows12`:

```sh
python3 -B scripts/boot-test.py artifacts/vm-build/windows12-amd64-preview.iso --timeout 300 --interval 30
```

The default output is a new `artifacts/boot-test-<timestamp>/` directory. An explicit `--output artifacts/boot-review-001` is allowed only when that directory does not exist. Paths escaping the project, symlink escapes, missing/non-ISO inputs, and reused output directories are refused. Relative paths are relative to the caller's current directory.

To attach a new disposable virtual disk for a later installer exercise:

```sh
python3 -B scripts/boot-test.py artifacts/vm-build/windows12-amd64-preview.iso --output artifacts/boot-with-disk-001 --installer-disk-size 24G --timeout 600
```

This creates only `disposable-install.qcow2` inside that new output directory. It does not launch or complete Calamares and supplies no keyboard automation. Existing disks are never accepted, reused or overwritten by this harness. Keep the disk for a future explicitly implemented installation test rather than treating its creation as installation success.

## Review evidence

- `screen-0000.ppm`, `screen-0001.ppm`, …: binary PPM screenshots. Inspect them with an image viewer supporting PPM. Early captures may show only firmware or boot menus; allow extra time under TCG.
- `serial.log`: guest serial output if the ISO enables a serial console. An empty file alone is not a failure or success.
- `qemu.log`: emulator diagnostics.
- `qmp-events.jsonl`: all QMP replies/events observed by the single client.
- `run.json`: running PID, exact command, ISO SHA256 and captures so far.
- `result.json`: final outcome, process return code and capture paths. It deliberately records `boot_verified: false` and `install_verified: false`.

The harness owns both QMP FIFOs (`qmp.in` and `qmp.out`). Do not attach a second QMP reader or writer while it runs. The process exits after the capture period and requests QEMU quit, falling back to terminate/kill with bounded waits. Ctrl+C performs the same cleanup and writes an interrupted result. On an externally killed run, use `run.json` to identify the process, verify its command before stopping it, and retain the output; do not reuse its directory.

Exit status zero means the capture loop completed, not that Linux reached a usable desktop. Human review must record the actual screens and failures. Installation acceptance additionally requires operating Calamares on a new contained disk, rebooting that installed disk without the ISO, creating a user and checking persistence/updates. Those actions are not implemented by this harness. UEFI/Secure Boot, physical devices, GPU acceleration, networking, Office sign-in and application usability also remain separate tests.

The `smm=off` setting follows a firmware boot-loop diagnosis in this restricted software-emulation environment. It is a harness workaround, not evidence for a physical platform's firmware behavior or Secure Boot support. No host changes are required.

## Status

Source implementation prepared for the first available project ISO. Serialization regression tests in `tests/test_boot_guard.py` cover lock contention and release, the capture-wide lock lifetime, live/stale/ambiguous legacy FIFOs, symlink controls and escaping state paths without launching QEMU. They require the build-VM marker and keep fixtures beneath the guest project. AST syntax checks passed during implementation; runtime test execution remains pending. No harness execution or boot result is claimed by this document. See project validation/state records for subsequent runs.
