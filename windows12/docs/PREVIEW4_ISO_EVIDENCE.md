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

The corrected D-I installation and ISO-free installed-root proof have passed, as recorded below. Live default-session Plasma login/workflows, installed desktop login/workflows, separate Calamares installation, UEFI/Secure Boot and physical hardware coverage remain pending. The installed-root proof does not establish a usable graphical session or general device support. No physical disk operation has been performed.

Keep the ISO, checksum manifest, original authenticated inputs, tool archives/locks, frozen source, package manifest and full logs independently preserved. Git preserves source/memory rather than these ignored generated artifacts.

## First actual live desktop review

`artifacts/live-desktop-001/` was booted from the unchanged ISO with TCG/max/standard VGA, no writable disk and no network. It reached systemd startup, live-user automatic login, and a black default Plasma Wayland screen. TTY3 worked. `screen-0008.ppm` shows llvmpipe thread faults; `screen-0009.ppm` shows SDDM successful user authentication and startplasma-wayland. Thread fault messages alone do not identify a causal CPU defect.

Transient changes existed only in the disposable live RAM overlay: GALLIUM_DRIVER=softpipe in /etc/environment; then Autologin Session=plasmax11.desktop in /etc/sddm.conf (a drop-in alone was overridden by that file); then user plasma-workspace/env/w12-test.sh exporting QT_QUICK_BACKEND=software and KWIN_COMPOSE=Q. The softpipe Wayland attempt logged a DRM framebuffer Invalid argument (`screen-0011.ppm`); X11 launch/process and renderer environment are shown in `screen-0017.ppm`.

The modified X11 session displayed a bottom panel (`screen-0019.ppm`), responding launcher/menu (`screen-0022.ppm`) and Dolphin home (`screen-0024.ppm`). Rendering remained degraded (black wallpaper/window decoration issues); no file-operation or general workflow pass is claimed. This is partial modified-session evidence, not a default ISO GUI pass. Operator stopped the owned VM; return0 and outcome operator-stopped are recorded in result.json. The temporary changes were not added to the ISO or source overlay.

Next diagnostic: a NEW unchanged-ISO guest using the explicit contained Nehalem/2D virtio-vga profile after guest tests. No inference about physical hardware, UEFI or graphics-driver support follows from these software-emulated failures or workarounds.

The new diagnostic-profile controller passed55 guest tests, byte-identical preview4 packaging/dpkg checks and confirmed shutdown in `artifacts/overlay-check-c11fb30393c6f70b20f9472002912b2f/`. Ordinary-permission attempt af7aacea0e12491fe6b08b7615d9a464 failed before VM launch on loopback access; the approved network-enabled retry passed. At that checkpoint, corrected installation session8231 was active in `artifacts/install-serial20-001/`; its later late-command failure is recorded below.

## Hybrid structure and installation follow-up

Authenticated xorriso metadata review in `.work/iso-media-review/` confirmed MBR isohybrid/GPT/APM structures,55aa MBR signature, bootable BIOS/UEFI ElTorito entries, and the embedded EFI partition with EFI/BOOT/BOOTX64.EFI and GRUBX64.EFI. File identity stayed unchanged. The report's GPT overlapping notation was retained, not diagnosed as corruption. PhysicalUSB and UEFI runtime remain untested.

Corrected D-I installation8231 passed its exact guard, partitioned/formatted the new vda, and progressed beyond filesystem copying into installed-root configuration. One software-emulated guest watchdog warning during tar copy was retained in the serial log; copy progress continued. Completion callback and ISO-free proof were pending at that intermediate checkpoint; the subsequent late-command failure is recorded below.

Actual Calamares configuration review used authenticated read-only unsquashfs data under `.work/calamares-review-001/` and002. Required gates include live-user pkexec launch, offline APT behavior, partition/account choices, GRUB installation, removal/autoremove preserving the desktop and overlay, ISO-free login/reboot, and independent session/render verification. It unpacks pristine SquashFS, so live RAM workarounds do not transfer to the target. This route needs its own runtime acceptance; the D-I harness cannot certify it.

## Late-verification correction

The serial20 test reached root copy and GRUB, then failed the custom late command. Exact initrd in-target analysis confirmed stdout is suppressed unless --pass-stdout is first argument; the unchanged package-status grep therefore saw no text. The controller fix preserves the exact check and adds serial xtrace. Prior owned controller was cooperatively stopped130 after PID/argv verification; disk/logs remain preserved. Fresh full installation93139 used `artifacts/install-passstdout-001/`; its eventual successful installed-root proof is recorded below. These are harness corrections; the ISO hash/content remains unchanged and no success marker is synthesized.

The passstdout retry's traced late verification passed, and `artifacts/install-passstdout-001/completion-callback.json` records the callback at Unix timestamp 1793981503.0225112. At an intermediate parent observation, installation session 93139 was still active at approximately 59 minutes elapsed, displaying 40% `remove-live-packages` after an earlier initramfs rebuild. At that moment the installation and disk-boot flags remained false: the callback did not establish completion. The installer subsequently completed cleanup and the separate ISO-free boot proof passed, as recorded below. No success marker was synthesized and no cleanup step was skipped.

## Exact installer cleanup source review

Read-only extraction from this ISO is retained under `.work/installer-cleanup-review-1793982496474838322/`, with the source ISO path/stat identity and archive hashes in `provenance.json`, and extraction output in `xorriso.log`. The project xorriso executable and its cached archive were compared against the authenticated tool lock before use. Only package data was inspected; no installer script was executed on the host. ISO size, inode and modification/change times remained unchanged.

| Exact ISO input | SHA256 |
|---|---|
| `/pool-udeb/main/l/live-installer/live-installer_58_amd64.udeb` | `b60df57cd03c6a13b853ef78360ea563020cf7fe04d4de999e1465d38a954b72` |
| `/pool-udeb/main/f/finish-install/finish-install_2.124_all.udeb` | `16580af7d2aca8db76485c58f750b2a7f9b466a2ecd4be68fe33f4dc22bee95c` |

The live-installer archive contains `usr/lib/finish-install.d/14remove-live-packages`, SHA256 `be8b7fe176a12ad0edfa94112133531ef880b56c884b6b35f1af9e10f0fa724b`. The ISO tree has no `/live/filesystem.packages-remove`, so the script uses its manual removal branch: it checks for live-specific packages and invokes `in-target apt-get --yes purge` for those still present. The ISO manifest includes live-boot, live-boot-initramfs-tools, live-config, live-config-systemd and calamares-settings-debian. If removal occurred, the script then invokes `in-target update-initramfs -k all -u`, followed by `in-target apt-get --yes autoremove`. Package removal hooks can add initramfs work before that explicit rebuild.

The finish-install archive also contains `usr/lib/finish-install.d/10update-initramfs`, SHA256 `804619a204e52220f893e81147acb2bba9897e833a483965869f0774102d913a`. It can request an earlier initramfs refresh for the cryptsetup/console-setup combination or loaded bochs/cirrus modules. Thus the transition from `update-initramfs` to `remove-live-packages` does not establish that all initramfs work has finished.

There is no explicit question in `14remove-live-packages`, and its APT calls supply `--yes`. `in-target` still uses the debconf passthrough frontend, so that flag alone cannot exclude every possible package-script question. At review time, the serial log showed the cleanup label and clock updates, without a new question or error. The later `20final-message` uses `finish-install/reboot_in_progress`, which the harness already preseeds.

These sources explained operations that could take time under TCG, without establishing a completion time. At that checkpoint, the parent's advancing write counters and busy QEMU process supported continued activity. The guest was preserved until cleanup and installer shutdown completed, followed by the separate ISO-free proof. Callback receipt was not substituted for either result.


## Successful BIOS installation and ISO-free installed-root boot

Owned controller session 93139 exited 0. `artifacts/install-passstdout-001/result.json` now records `outcome: installed-root-boot-proof-passed`, `completion_callback: true`, `install_verified: true` and `disk_boot_verified: true`. Both `install_run` and `boot_run` returned 0 without timing out. The result finished at Unix timestamp 1793983164.8832436, or 2026-11-06 16:39:24 UTC.

The installation used the unchanged preview4 ISO and a new project-contained virtual disk. `artifacts/install-passstdout-001/installed-boot-run.json` records the second BIOS/TCG invocation with only that disk, `-boot order=c` and `-nic none`: no ISO, direct kernel/initrd or host share was attached. Its serial evidence is `artifacts/install-passstdout-001/installed-boot-serial.log`, including the matching one-shot token:

```text
WINDOWS12_INSTALLED_BOOT_OK:267337ed9a77d14b8f246bf4 root=/dev/vda1 package=0.1.0~preview4 proof_once=267337ed9a77d14b8f246bf4
```

The matching configuration marker and `configuration_audit` report `graphical.target`, `sddm.service`, `/usr/bin/sddm`, and absence of the known transient build CA and proxy entries. The proof also checked the installed desktop package and test account. `proof_service_one_shot` and `proof_stamp_reported` are true. These are installed-root/configuration checks, not evidence that SDDM or Plasma rendered or accepted a graphical login.

The stopped standalone baseline is retained at `artifacts/install-passstdout-001/disposable-install.qcow2`:

- File size: 9,391,964,160 bytes.
- Sealed SHA256: `58bcaea9b07c88797ac80fd8aed126862a1459561d061763a94764fecf74ffad`.
- Producer seal identity: device 66306, inode 10092574, mtime_ns 1793983146184567999.

`gui_verified` and `configuration_audit.gui_runtime_verified` remain false. Default live/installed desktop workflows, Calamares installation, UEFI runtime, Secure Boot and hardware acceptance remain separate pending gates. The baseline must be preserved; later graphical review uses a fresh writable child above its explicit read-only graph.

The expanded KVM/normal-UEFI/manual-disk controller suite is now running in a separate contained check VM, owner session 19616, log `.work/overlay-check.log`. Its result is pending at this checkpoint; source review and firmware input verification do not constitute its runtime pass. No host setup or physical-disk action occurred.


## Expanded harness checks

The first expanded run2e5f15f759bd4fbc5a770de8f78cd814 ran82 tests but stopped1 on two manual-review fixture failures. The fixture patched contextlib wrapper globals instead of exclusive_runner.__wrapped__.__globals__; no runtime lock was removed or mocked away. After correcting only the test fixture, artifacts/overlay-check-cab87aa07f654e7123fe1234a8e50838 passed all82 guest tests, deterministic9970-byte preview4 package/dpkg checks and confirmed QEMU shutdown. Source SHA256b5cab90cce74b440d596cb68636ccb4b0d8d26c9a5beed9032f10955ae838434; package hash remains cf4652f5ef2054388a6377e908c2673c78a7c003cee9362e003a9c61f4aa8075. Installed GUI session51793 is now active in artifacts/installed-desktop-virtio-001 using KVM/host/plain2Dvirtio and a NEW child over the sealed baseline; actual login/workflow evidence is pending.


## Installed desktop and normal live installer follow-up

Actual default installed Wayland desktop review completed0 with unchanged baseline; docs/INSTALLED_DESKTOP_PREVIEW4.md records login/layout/menu/file editing, basic offline DOCX save/reopen, lock/unlock and logout/relogin, exported public files/hashes and remaining workflow limits. Automatic harness flags remainfalse; manually reviewed observations are separate. A new pristine-ISO KVM/host/virtio live guest75984 rendered its default desktop without guest graphics tweaks and launched Calamares from Install Debian. Its actual offline installation is now copying to the only new24GiB virtual disk after reviewed partition/account summary. Evidence artifacts/calamares-live-001; completion, Calamares-installed ISO-free boot and UEFI validation remain pending.


Normal UEFI live boot subsequently reached the default Wayland desktop and offline guide; controller55315 stopped0 with original firmware inputs unchanged (docs/UEFI_PREVIEW4.md). All97 integrated source tests/package/shutdown passed in artifacts/overlay-check-196e24e1e16eef4083a3ff138c4ab309. New clock-fixed full build is next; the original ISO remains unchanged and lacks util-linux-extra. UEFI installed-disk and next-image acceptance remain pending.
