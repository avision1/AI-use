# Preview4 normal Calamares installation review

Checkpoint: offline Calamares completion and initial ISO-free installed desktop/account observations, 2026-11-06. The installed review completed0/guest-exited with baseline_unchanged=true in both result.json and manual-review.json, and no setup/cleanup/baseline error. Another independent reboot and broader application workflows remain pending. Reviewed observations below are separate from the harness's automatic flags, which remain false.

## Image and contained environment

The unchanged ISO is `artifacts/vm-build/windows12-amd64-preview.iso`, SHA256 `7d36b5847fba7240ee2795bb42ff3ea841652569b7eb983cfec6ea96968ae11c`. Its checksum/content audit and separate BIOS D-I installation/ISO-free root proof are documented in [PREVIEW4_ISO_EVIDENCE.md](PREVIEW4_ISO_EVIDENCE.md). Those results do not establish that the Calamares installation path works.

This manual run is `artifacts/calamares-live-001/`, owned controller session 75984. Its `run.json` records KVM with the host CPU, two virtual CPUs, 4096 MiB memory, plain 2D virtio graphics, SeaBIOS, and a 7200-second deadline. The guest has no network interface (`-nic none`), no host share, and exactly one new writable 24 GiB virtual disk, exposed as `/dev/vda`:

`artifacts/calamares-live-001/disposable-install.qcow2`

The ISO is read-only. No host disk, host boot setting, host package, GPU passthrough, or physical installation is involved. The earlier proven D-I baseline at `artifacts/install-passstdout-001/disposable-install.qcow2` is separate and remains preserved.

## Observed normal GUI flow

Original PPM captures and command/QMP records are retained in the run directory. The following observations were reported by the parent after inspecting the actual captures; no target code was executed on the host for this document.

| Capture | Reviewed observation |
|---|---|
| `screen-0004.ppm` | The pristine ISO's default live Wayland desktop rendered its wallpaper, bottom panel, welcome content, and Install Debian icon. No temporary guest rendering/session changes were applied in this run. |
| `screen-0007.ppm` | The normal Install Debian desktop icon/wrapper launched the Calamares welcome page. |
| `screen-0011.ppm` | America/Chicago location and US locale choices were displayed. |
| `screen-0013.ppm` | US keyboard with the default Generic 105-key model was selected. |
| `screen-0015.ppm` | The partition page exposed only the new 24 GiB `/dev/vda` disk. |
| `screen-0017.ppm` | Erase-disk installation selected ext4 with the MBR/MSDOS route and no encryption. This applies only to the empty disposable virtual disk. |
| `screen-0020.ppm` | The public QA account entries were accepted, with green validation indicators; autologin was not selected. |
| `screen-0022.ppm` | The summary listed an MSDOS partition table, a 24575 MiB ext4 root partition with boot flag, and GRUB on `/dev/vda`. |
| `screen-0023.ppm` → `screen-0024.ppm` | The Install button was activated, followed by actual installation progress at 5%, “Filling up filesystems.” No intervening confirmation modal was observed in this interaction. This does not assert that every installer choice or configuration has no further confirmation. |
| `screen-0025.ppm` | The progress-page log toggle exposed installation output. |
| `screen-0034.ppm` | Calamares displayed its All Done completion page. |
| `screen-0039.ppm` | The subsequent standard live shutdown requested media removal and Enter; Enter completed the clean poweroff. |

The deliberately nonsecret disposable-account settings are login `w12qa`, password `Preview-Test-2026`, and hostname `windows12-qa`, with no autologin or encryption. These are QA fixtures, not credentials supplied for a real deployment. The subsequent installed login accepted this password; administration authorization is still being checked.

## Completion log and clock warning

The preserved `artifacts/calamares-live-001/calamares-session.log` is 74,471 bytes, SHA256 `ba53e8b10fb146d5e0dbf30065b80327e09363f1746a8a4bdefcde8b2802e63b`. Its gzip export has SHA256 `146a5b78300eb55e15b8e9208153f57d6a840aa9d69dc854ce19e41a96bf6a81`. The log records GRUB installation, package purge/autoremove, job 39 of 39, and `completion: succeeded`. Together with the reviewed All Done page, this establishes completion of this offline BIOS Calamares run. Controller 75984 subsequently exited 0 with `guest-exited` and no errors after the standard live-media shutdown interaction.

Lines 797–804 record two `hwclock` calls exiting 127 because the target executable is absent. Calamares continues to the remaining jobs; its generic BIOS/kernel warning does not establish a hardware fault. Debian 13 supplies `/usr/sbin/hwclock` in [util-linux-extra](https://packages.debian.org/trixie/amd64/util-linux-extra/filelist), which is absent from this ISO's package manifest. A future-candidate source change adds that package to the image list and required ISO core packages. The current ISO and its checksum remain unchanged; that source change has not been built or validated in a replacement ISO.

## ISO-free installed review in progress

The completed controller was12720, `artifacts/calamares-installed-review-001/`. `scripts/manual-disk-review.py` recorded a new baseline seal in `manual-source.json`, retained the stopped Calamares disk read-only, and booted a new writable child using BIOS without an ISO, direct kernel/initrd, or network interface. This is distinct from the earlier D-I installation proof. Final clean shutdown and baseline integrity verification PASSED. The baseline is9223077888bytes, SHA2562deeddcf9bd4e3a84cf9491d0c6defd85383dddfa34bac75592dcf67c54338a5. No VM is active at this checkpoint.

| Installed-review capture | Reviewed observation |
|---|---|
| `screen-0002.ppm` | The ISO-free disk boot reached SDDM with account `w12qa` and a Wayland session. |
| `screen-0003.ppm` | Login with the selected public QA password reached the desktop wallpaper and panel. |
| `screen-0006.ppm` | Terminal output identified `w12qa` in the `sudo` group, hostname `windows12-qa`, a Wayland session, root `/dev/vda1`, and timezone America/Chicago. Chromium, LibreOffice Writer and `windows12-desktop` reported installed status; `getent passwd user` returned no live account; `systemctl --failed` reported zero failed units. |
| `screen-0007.ppm` | LibreOffice Calc opened in the installed session. |
| `screen-0008.ppm` | Cells containing 10 and 20, with `SUM(A1:A2)`, produced 30. |
| `screen-0009.ppm` → `screen-0011.ppm` | The save dialog selected Excel 2007–365 format and the format confirmation was accepted. |
| `screen-0013.ppm` | The saved XLSX reopened with result 30. |
| `screen-0016.ppm` | The selected formula was captured for review. |

The selected public password successfully authorized `sudo -v`. The serial root audit emitted `W12_CAL_ROOT_BEGIN` with uid 0/root, hostname `windows12-qa` and timezone America/Chicago. This supplies actual administration authorization evidence in addition to group membership.

The public spreadsheet was exported through the serial `W12_XLSX` transfer after an operator focus retry; that retry did not identify a distribution error. Retained output `artifacts/calamares-installed-review-001/public-files/calamares-check.xlsx` is 5,208 bytes, SHA256 `5ede1da77fddaedf1585719159097df192ff8140eb8eff95e045a98daeb77678`; its manifest is retained with the artifacts. Inspection of ZIP member `xl/worksheets/sheet1.xml` verified formula `SUM(A1:A2)` and cached value 30. This is one basic Calc save/reopen/export check, not the full Office fixture corpus, PDF testing or a broad compatibility claim.

`sudo poweroff` has been sent to controller 12720's guest, but final controller termination and baseline preservation have not yet been confirmed. Additional cleanup checks, locale/keyboard persistence and another clean reboot still need evidence. All automatic verification flags remain false; the manually reviewed observations above do not alter them.

Future UEFI harness source changes are integrated but have not been tested in a guest. Normal UEFI installation/boot, Secure Boot and physical hardware support remain pending. This evidence covers this contained BIOS run and does not certify other hardware or broad Office document compatibility.
