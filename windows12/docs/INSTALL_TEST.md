# Disposable Debian live-installer test

`scripts/install-test.py` prepares an unattended **Debian Installer (D-I)** installation from this project's live ISO, then boots its new virtual disk without the ISO. This tests the ISO's D-I live-installer route. It does not exercise Calamares or certify a graphical login, Office, hardware, UEFI or Secure Boot.

No execution is claimed here. The harness must wait for an actual ISO, and must not compete with an active source-build VM for resources. Read PROJECT_STATE.md and check running jobs first.

## Requirements and invocation

From `AI-use/windows12`, after the source-build VM has stopped and produced its ISO:

```sh
python3 -B scripts/build-tools.py --profile iso
python3 -B scripts/install-test.py artifacts/vm-build/windows12-amd64-preview.iso --install-timeout 3600 --boot-timeout 600
```

The existing authenticated QEMU toolset under `.work/builder/tools` is required. The separate ISO-tool profile supplies xorriso without changing that running toolset. The harness checks the cached .deb SHA256 against its authenticated bootstrap lock, uses read-only `dpkg-deb --fsys-tarfile` decompression into memory, and compares the extracted xorriso executable before using it. This supports Ubuntu archives containing `data.tar.zst` without requiring Python tarfile zstd support; it installs or extracts no package to the host. It lists the actual ISO file tree and discovers a co-located `vmlinuz` / `initrd.gz` pair rather than assuming an installer path. If several equally shallow candidates exist, inspect `iso-tree-files.txt` and use the observed directory:

```sh
python3 -B scripts/install-test.py artifacts/vm-build/windows12-amd64-preview.iso --output artifacts/install-review-002 --installer-directory /observed-installer-directory
```

Do not substitute the example directory without reading the listing. Discovery deliberately fails if no conventional D-I pair exists; it does not silently use the live kernel or guess another architecture.

Each invocation requires a new output directory (default `artifacts/install-test-<timestamp>/`) and creates only `disposable-install.qcow2` there. Default virtual capacity is 24 GiB; `--disk-size 32G` changes the new disk's virtual capacity. Check host free space first: sparse capacity is not reserved physical space, and an installation can consume several GiB. There is no existing-disk or resume argument. A failed disk is retained for investigation rather than erased automatically. Before creating the output or disk, the harness requires free space of at least `max(8 GiB, 3 × ISO file size)`. This is a conservative heuristic, not an assurance that every installation fits. If it refuses, preserve source, logs and required artifacts, then deliberately reclaim reproducible build working storage or use a larger compliant workspace. The harness never removes builder storage.

## Boundary and installation guards

- ISO, outputs, tools, extracted kernel/initrd, caches, profiles, serial files and screenshots must resolve beneath `windows12`. Symlink escapes and reused outputs are refused.
- Before output/disk creation, the harness acquires and holds the source builder's `.work/builder/runner.lock`. It also probes the legacy builder input FIFO for an active reader, without sending commands or consuming QMP output. A held lock, active legacy listener, or ambiguous control files causes refusal. This covers the earlier source-build runner that did not yet use flock; do not delete its FIFOs to bypass the check.
- QEMU exposes exactly one newly created virtio disk plus the read-only ISO. It receives no host block devices or host filesystem shares.
- D-I is preseeded to partition **only `/dev/vda`**. Before partitioning, the guest checks that it has exactly the expected disk name and the unique QEMU virtio serial. A mismatch requests immediate poweroff and blocks continuation. The late command repeats the guard.
- The HTTP server binds host loopback and serves only the run's exact preseed path, late-script path and completion callback. It exposes no directory listing or arbitrary file endpoint. Installation uses QEMU user networking to reach this service; no inbound guest ports are forwarded. The preseed explicitly skips mirror selection, disables an APT network mirror and optional security-service fetching so installation uses the ISO's live filesystem. An invalid mirror hostname is only a secondary fail-safe; it is not the mechanism used to request offline installation.
- Public disposable credentials are `testuser` / `testpass`, with no root login. These are intentionally nonsecret test fixtures. Never use the preseed or resulting disk for a real deployment, connected account or physical installation.

This safety model relies primarily on which disks QEMU exposes. The additional guest serial/name guard is fail closed if the expected sysfs serial attribute is unavailable. Do not relax it to make a failed test pass without investigating the guest.

## What counts as success

The harness does not accept QEMU exit status zero alone. It requires:

1. The D-I late command verifies the installed Debian root and installed `windows12-desktop` package, prepares a test-only first-boot proof service, and reaches the run-specific completion callback.
2. The installer VM shuts down without timeout or emulator failure.
3. A second, separate QEMU invocation starts the new disk with **no ISO, direct kernel/initrd, network interface or host share**.
4. The installed system's systemd proof service confirms its root is a `/dev/vda` partition, Debian identity exists, the overlay package is installed and `testuser` exists. It rejects known `windows12-build-proxy.crt` / `.pem` trust artifacts and active proxy entries containing `10.0.2.2` beneath `/etc/apt` or in `/etc/environment`. Missing optional files are handled safely; ordinary Debian repository URLs are not rejected. It also requires the configured default target to be `graphical.target` and the display-manager unit to resolve to SDDM, checking `/etc/X11/default-display-manager` when present. These are configuration audits, not a claim that SDDM or Plasma displayed successfully. The service writes run-specific configuration and root/package serial markers, then powers off.
5. The marker and clean second shutdown are both observed.

Only then does `result.json` record `install_verified: true` and `disk_boot_verified: true`. It records the configuration evidence under `configuration_audit`, including the configured target/display manager and absence of the known build proxy/CA artifacts. It always leaves `gui_verified: false` and `gui_runtime_verified: false`. This proof establishes an installed-root system boot and the specified package/account checks. It does not establish a usable desktop, password authentication, privileges, updates, recovery or application functionality.

The proof service modifies only the disposable installed disk, not the ISO. It remains enabled and will request poweroff on subsequent successful boots; this disk is a test artifact, not a user installation. A future interactive test should create a fresh disk or deliberately disable the test service within a contained VM.

## Evidence and recovery

Retain `result.json`, ISO SHA256, `iso-tree-files.txt`, `xorriso.log`, `preseed.cfg`, `late-install.sh`, completion callback, exact per-stage QEMU commands/PIDs, serial logs, QMP events and PPM screenshots. Installer prompts or errors appear primarily in `install-serial.log`. The second boot's required root and configuration markers are in `installed-boot-serial.log`; that file may otherwise be quiet because no persistent serial-console GRUB settings are injected.

Each stage owns one QMP FIFO client. Do not attach another reader/writer. Timeout or Ctrl+C requests QEMU quit, then terminate/kill if necessary; results and disk are preserved. If an external kill interrupts Python, inspect the recorded per-stage PID and command before stopping any surviving VM. Never start a duplicate VM using the same disk.

If D-I asks for media, missing components, mirror access or confirmation, this is a failed unattended test to diagnose. Do not claim installation support from the presence of installer packages. Under TCG, installation can take substantially longer than a hardware-assisted VM; increase the timeout only when logs show actual progress.

## Primary basis

Debian trixie's documented preseed settings and late-command mechanism were consulted on 2026-10-23: https://www.debian.org/releases/trixie/amd64/apbs04.en.html . The live-installer route copies the live filesystem instead of assembling a separate default package installation: https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-installer.en.html . This harness's guard, callback and first-boot proof are project test code, not upstream certification.
