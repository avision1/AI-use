# Validation record and release gate

This is a development preview. A source recipe, launchers, or successful unit tests are not evidence of a bootable/installable OS. PROJECT_STATE and artifact logs record actual results; unchecked items below remain unverified.

## Automated contained checks

- Run `python3 -B -m unittest discover -s tests -v` inside the build VM. Browser invocation is mocked: these checks cover allowlists, argument handling, root refusal, fallback/errors and payload consistency only.
- Run `python3 -B scripts/package-desktop.py` inside the VM, inspect with `dpkg-deb --info` and `--contents`, build twice and compare SHA256. Confirm script modes and all paths.
- Validate `.desktop` entries using desktop-file-validate inside the image environment.
- Build ISO using signed inputs. Preserve package list, source revision, tools/input digests, complete build log and ISO checksum.
- Inspect image contents and boot entries. Repeated procedure is required; byte-identical full ISOs are not yet guaranteed because live-build fetches mutable packages and embeds timestamps.

## Desktop smoke test in disposable VM

Boot first without installation. Confirm visible desktop, launcher, bottom taskbar/pins, tray, clock and wallpaper. Check double-click and file creation, copy/move/trash/restore in Dolphin; open Settings, Discover, Konsole, PDFs, archives and LibreOffice. Restart session and confirm no duplicate panels or lost user changes. Check display scaling and keyboard navigation. Capture VM screenshots/logs under artifacts/.

Open each web launcher in a regular user account; verify official service domain, login handling and sign-out. Do not record credentials or private documents. Authenticated Office tests require the user's eligible account and user participation; never substitute automated mock tests. Create/edit/export a disposable Word document, Excel workbook and PowerPoint presentation; check offline loss/recovery. Explicitly record unavailable features, tenant restrictions and formatting differences.

## Installer smoke test

Use only a new virtual disk under windows12/.work or artifacts. Test BIOS and UEFI separately, install using Calamares, shut down, detach ISO, boot installed disk and inspect `/etc/os-release`, network, users, package database, target launchers, package updates and reboot. Check that live-user configuration/credentials did not migrate. Do not test against host disks or physical hardware.

## Separate coverage needed

Secure Boot, encryption, dual boot, Windows application versions, 32-bit runtimes, anti-cheat games, GPU/Wi-Fi/Bluetooth drivers, printers, suspend/resume, accessibility and localization require individual results. None is certified by the initial VM build. Keep compatibility claims tied to exact OS/app/device versions and dated evidence.

## Build failure recovery

Before restarting, check build process and serial logs plus guest exit marker. Preserve failed logs. Do not reuse an incomplete release ISO as a valid artifact. Fix the error, checkpoint code/state, then retry from documented inputs. No automatic physical installation or host fallback is permitted.
