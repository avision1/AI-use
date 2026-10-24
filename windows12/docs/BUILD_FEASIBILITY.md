# Contained build feasibility

Checked 2026-10-23 (America/Chicago). This is a source-build pipeline, not a completed release.

## Observed

- No initial QEMU, Podman/Docker, live-build, xorriso, squashfs utilities, or `/dev/kvm`.
- User namespace mapping is denied; bubblewrap namespace setup fails; Landlock returns ENOSYS. Do not use host chroot, host mounts, or globally installed packages as a fallback.
- Project-local QEMU dependencies were downloaded from Ubuntu 24.04 signed InRelease/Packages metadata. SHA256 checks protect each package; packages are unpacked, never installed. Python tar `data` filtering avoids unmapped UID/GID chown failures and external symlink targets. `build/tools-lock.json` records exact package versions, filenames and hashes.
- QEMU TCG firmware ran for ten seconds with no disk/network. Two BIOS attempts then stalled in an identical SMM handler; `smm=off` resolved the stall. Debian cloud guest subsequently booted Linux/systemd, grew its root filesystem to 20 GiB and ran cloud-init/our build script. This establishes real guest execution, not derivative desktop or installer success. The genericcloud kernel lacks 9p, so the initial output-share mount failed; the implementation now uses narrow HTTP artifact export instead.
- The execution environment assigns fresh loopback proxy ports to each tool invocation. Never hardcode a port copied from an earlier call. `build-vm.py` reads the current process HTTPS proxy and translates its loopback host to QEMU's host alias `10.0.2.2`.

## Build design

`python3 scripts/build-tools.py` prepares local QEMU tools on an amd64 Ubuntu 24.04 host. It reads the host Ubuntu archive verification key without changing it. It deliberately does not invoke apt install or run package maintainer scripts.

`python3 scripts/build-vm.py --probe` starts a diskless, networkless ten-second TCG process. The absence of KVM slows builds but does not preclude emulation.

`python3 scripts/build-vm.py --prepare` downloads Debian 13 genericcloud amd64 and checks SHA512 against the official HTTPS manifest. **Detached Debian image signatures are not yet verified**; this is HTTPS origin authentication plus transfer integrity, not an independently signed input chain. The cached manifest pins subsequent invocations; preserve it and the qcow2 for reconstruction.

`python3 scripts/build-vm.py` creates a 20 GiB virtual qcow2 disk backed by the checked cloud image, serves exact source snapshots and NoCloud seed data through a loopback HTTP server, and boots QEMU TCG. The VM has no host block devices or host filesystem shares. All guest root, `/etc`, `/usr`, package caches, chroots and mount points live in the project-contained virtual disk. Completed outputs are streamed over HTTP PUT to an exact-filename allowlist under `artifacts/vm-build/`, with bounded Content-Length, symlink/escape rejection and atomic `.part` replacement. The host checks the exported ISO digest before declaring a completed build.

The guest runs overlay unit tests, packages `windows12-desktop` twice and compares digests, inspects the Debian package, then builds a Debian trixie amd64 KDE live ISO with live-build and Calamares. The desktop package is installed through `config/packages.chroot` so dpkg tracks its ownership. No arbitrary host source share or host installer is exposed. The ISO is moved into the guest export directory, avoiding a second full copy on the 20 GiB disk. Guest commands refuse execution without the VM marker.

## Outputs and limitations

- Ignored intermediate storage: `.work/builder/` (authenticated packages and metadata, local tools, original cloud image, VM disk, tar source snapshots).
- Ignored outputs: `artifacts/vm-build/` (serial/guest logs, package, ISO if successful, checksums, provenance, exit code).
- A successful build is not a release gate: BIOS and UEFI live boot, disposable VM installation, installed reboot, GUI and service validation are still required; see `VALIDATION.md`.
- This pipeline currently resolves distribution package repositories at build time, so the resulting OS image is not yet byte-for-byte reproducible. The source snapshot, signed repository metadata, package manifest, source lock and output hashes identify the build; frozen Debian snapshot mirrors are still needed for long-term reproducibility.
- Tool bootstrap supports the current amd64 Ubuntu 24.04 build host only. Other hosts need compatible QEMU tools without global installation.
- Debian builder guest boot, filesystem growth, NoCloud seed retrieval and execution of the guest script are observed. Overlay unit tests, packaging gates, guest repository/proxy access, the revised HTTP export, live-build recipe, derivative boot, installer and Office service login remain unverified until their actual logs establish success. There is no ISO yet at this checkpoint.

## Job control and interrupted runs

`python3 scripts/probe-qmp.py status` queries the running VM; `registers` diagnoses CPU state; `quit` stops it without host PID assumptions. QMP uses project-local FIFOs. Managed tool calls have separate PID namespaces, so a PID read from `/proc` may not be signalable from another tool call. The original exec session can also be stopped with its Ctrl-C mechanism.

`python3 scripts/build-vm.py --resume` boots the preserved disk with a fresh NoCloud instance-id, refreshed current proxy port, and the original frozen `checks.tar` whose SHA256 is checked against `build-source.sha256`. It reruns the archived guest build script against cached guest working directories; it is not instruction-level suspend/resume. Changed working-tree sources are not silently mixed into that build. To build changed sources, deliberately preserve the old disk/snapshot and start a new build. Live-build rerun recovery itself remains unverified.
