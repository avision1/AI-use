# Preview4 ISO evidence — 2026-11-06

An actual hybrid amd64 ISO exists at `artifacts/vm-build/windows12-amd64-preview.iso` (ignored generated output; not uploaded to Git).

- Size: 3,579,805,696 bytes.
- SHA256: `7d36b5847fba7240ee2795bb42ff3ea841652569b7eb983cfec6ea96968ae11c`.
- Frozen source archive SHA256: `027051ef7e6da1be12cabb3664a06ce5be0801a307acfc89bd7cb2dfa288b6e9`.
- Build exit: 0; builder stopped. Source/provenance/logs and adjacent SHA256SUMS retained in `.work/builder/` and `artifacts/vm-build/`.
- Base: Debian13 amd64; desktop package0.1.0~preview4.

## Measured validation

`artifacts/candidate-gates-1793950554450406600/audit/result.json` passed the checksum/content audit against frozen source. It verified managed file hashes/modes, required Plasma/SDDM/Calamares/LibreOffice/browser packages, independent Linux help, and absence of known transient build proxy/CA files. El Torito lists bootable BIOS and UEFI entries; structure is not runtime UEFI proof.

BIOS capture reached the ISO boot menu. Independently reviewed original screenshot: `artifacts/candidate-gates-1793950554450406600/bios/screen-0010.ppm`. It shows Live system, fail-safe, and installer options; no key was sent by the capture-only harness. This proves a BIOS boot menu, not a running desktop.

The first automated D-I test stopped before partitioning with `WRONG_DISK_GUARD`; no installation was certified. Evidence: `artifacts/candidate-gates-1793950554450406600/install/`. Its harness generated a27-byte serial; virtio-blk exposes20bytes. The fix limits the disk ID to `W12` +17hex characters while keeping the full24hex token for callbacks/installed-boot proof, and updates the GUI provenance reader. The exact single-disk/name/serial guard remains enforced.

Primary serial-limit implementation references: https://raw.githubusercontent.com/qemu/qemu/v8.2.0/hw/block/virtio-blk.c (GET_ID) and https://raw.githubusercontent.com/torvalds/linux/v6.12/include/uapi/linux/virtio_blk.h (VIRTIO_BLK_ID_BYTES).

The corrected controllers passed all52 tests in the disposable guest, deterministic double packaging and dpkg inspection; guest shutdown confirmed. Evidence: `artifacts/overlay-check-5c78814e281bf549335a6647bffc1de9/`, source SHA256 `3ab2bd35eb5c9269b48f65f34a67455fc8bd211f5dd3b416782e3f0d14192524`. This host-only harness fix does not alter the existing ISO.

## Remaining acceptance

Fresh corrected D-I installation and ISO-free installed-root proof; live Plasma login/workflows; installed desktop login/workflows; separate Calamares installation; UEFI/Secure Boot and physical hardware coverage. Do not recommend replacing an existing computer OS based only on the successful content audit and boot menu. No physical disk operation has been performed.

Keep the ISO, checksum manifest, original authenticated inputs, tool archives/locks, frozen source, package manifest and full logs independently preserved. Git preserves source/memory rather than these ignored generated artifacts.

## First actual live desktop review

`artifacts/live-desktop-001/` was booted from the unchanged ISO with TCG/max/standard VGA, no writable disk and no network. It reached systemd startup, live-user automatic login, and a black default Plasma Wayland screen. TTY3 worked. `screen-0008.ppm` shows llvmpipe thread faults; `screen-0009.ppm` shows SDDM successful user authentication and startplasma-wayland. Thread fault messages alone do not identify a causal CPU defect.

Transient changes existed only in the disposable live RAM overlay: GALLIUM_DRIVER=softpipe in /etc/environment; then Autologin Session=plasmax11.desktop in /etc/sddm.conf (a drop-in alone was overridden by that file); then user plasma-workspace/env/w12-test.sh exporting QT_QUICK_BACKEND=software and KWIN_COMPOSE=Q. The softpipe Wayland attempt logged a DRM framebuffer Invalid argument (`screen-0011.ppm`); X11 launch/process and renderer environment are shown in `screen-0017.ppm`.

The modified X11 session displayed a bottom panel (`screen-0019.ppm`), responding launcher/menu (`screen-0022.ppm`) and Dolphin home (`screen-0024.ppm`). Rendering remained degraded (black wallpaper/window decoration issues); no file-operation or general workflow pass is claimed. This is partial modified-session evidence, not a default ISO GUI pass. Operator stopped the owned VM; return0 and outcome operator-stopped are recorded in result.json. The temporary changes were not added to the ISO or source overlay.

Next diagnostic: a NEW unchanged-ISO guest using the explicit contained Nehalem/2D virtio-vga profile after guest tests. No inference about physical hardware, UEFI or graphics-driver support follows from these software-emulated failures or workarounds.

The new diagnostic-profile controller passed55 guest tests, byte-identical preview4 packaging/dpkg checks and confirmed shutdown in `artifacts/overlay-check-c11fb30393c6f70b20f9472002912b2f/`. Ordinary-permission attempt af7aacea0e12491fe6b08b7615d9a464 failed before VM launch on loopback access; the approved network-enabled retry passed. Corrected installation session8231 is now active in `artifacts/install-serial20-001/`; its eventual result must be inspected, not presumed.

## Hybrid structure and installation follow-up

Authenticated xorriso metadata review in `.work/iso-media-review/` confirmed MBR isohybrid/GPT/APM structures,55aa MBR signature, bootable BIOS/UEFI ElTorito entries, and the embedded EFI partition with EFI/BOOT/BOOTX64.EFI and GRUBX64.EFI. File identity stayed unchanged. The report's GPT overlapping notation was retained, not diagnosed as corruption. PhysicalUSB and UEFI runtime remain untested.

Corrected D-I installation8231 passed its exact guard, partitioned/formatted the new vda, and progressed beyond filesystem copying into installed-root configuration. One software-emulated guest watchdog warning during tar copy was retained in the serial log; copy progress continued. Completion callback and ISO-free proof are still pending.

Actual Calamares configuration review used authenticated read-only unsquashfs data under `.work/calamares-review-001/` and002. Required gates include live-user pkexec launch, offline APT behavior, partition/account choices, GRUB installation, removal/autoremove preserving the desktop and overlay, ISO-free login/reboot, and independent session/render verification. It unpacks pristine SquashFS, so live RAM workarounds do not transfer to the target. This route needs its own runtime acceptance; the D-I harness cannot certify it.

## Late-verification correction

The serial20 test reached root copy and GRUB, then failed the custom late command. Exact initrd in-target analysis confirmed stdout is suppressed unless --pass-stdout is first argument; the unchanged package-status grep therefore saw no text. The controller fix preserves the exact check and adds serial xtrace. Prior owned controller was cooperatively stopped130 after PID/argv verification; disk/logs remain preserved. New full installation93139 in artifacts/install-passstdout-001 is pending. These are harness corrections; the ISO hash/content remains unchanged and no success marker is synthesized.

The passstdout retry's traced late verification passed, and completion-callback.json was received. At the latest observation, D-I was still regenerating the installed target initramfs. Callback alone does not establish completed installation or ISO-free boot; all such flags remain pending. Expanded KVM/normalUEFI/manual-disk source is reviewed and syntax-checked, with actual firmware archive/input comparison passed, but expanded guest/runtime validation is queued behind this exact installer. No host setup or physical-disk action occurred.
