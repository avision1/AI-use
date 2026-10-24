# Guest live-build recipe review

Review date: 2026-10-23 (America/Chicago). Read-only review of `build/guest-build.sh`, the desktop package generator and current build orchestration. No implementation changes, host package installation, host tests or installation performed. This is a source review, not a successful build/boot/install report.

## Findings

| Priority | Finding | Action |
|---|---|---|
| High | The 20 GiB guest build disk has little predictable margin for a full KDE task, LibreOffice, Chromium and Firefox, recommended packages, cached downloads, expanded chroot, squashfs and ISO staging. Actual peak use is not measured yet. | Before `lb build`, record `df -h /` and guest disk layout. Monitor space during chroot and binary stages. Consider a larger contained virtual disk only if host free space permits. Do not discard caches or reduce recommended packages blindly: live-config/user setup and desktop integrations can depend on them. |
| Medium | Default squashfs compression is xz [R1], potentially slow in a full TCG guest. This affects build duration more than correctness. | Consider explicit `--chroot-squashfs-compression-type zstd` for preview builds and record the choice. Keep output-size and memory observations. No compression-speed benchmark was performed here. |
| Medium | Input package versions resolve from moving trixie mirrors. The final package manifest records resolved versions but does not by itself guarantee those versions remain downloadable. | Describe this release as a repeatable recipe, not byte-reproducible. Preserve package manifest, build config, tool/input provenance and logs. Later pin a snapshot and source epoch for reproducibility. |
| Medium | SDDM/default graphical target and installer behavior are inherited rather than asserted in a final image audit. Source package relationships look consistent, but a passing package list is not a successful desktop. | Inspect target `/etc/X11/default-display-manager`, enabled display-manager service, default target and live-config autologin. Boot and install to a disposable disk. Verify live user `user` is removed or disabled in the installed system and chosen user privileges are correct. |
| Medium | The proxy cleanup hook removes a specifically named apt configuration and CA; environment-derived live-build proxy files may use other generated names. No leak is demonstrated by this review. | Audit final chroot/ISO apt configuration and CA trust for `10.0.2.2`, build proxy URLs and the infrastructure certificate. Do not assert cleanup from the hook's existence alone. |
| Low | `--debian-installer live` adds Debian Installer alongside Calamares; it is not what enables Calamares. This expands build work and boot-menu paths. | Keep both only intentionally and test each advertised entry. Calamares comes from its installed packages. Do not present untested Debian Installer boot entries as validated alternatives. |

A combined space estimate is deliberately not given as a measured number: actual filesystem reuse/hardlinks, package selection and caches affect the peak. The risk is the sum of simultaneous build layers, not merely the final ISO size.

## Checks that found no immediate recipe blocker

- `--architectures` and `--binary-images` are accepted aliases in the actual trixie live-build `1:20250505+deb13u1` package frontend, although the manpage synopsis uses singular forms. The package was inspected as data in memory, not installed or executed.
- `task-kde-desktop` and `calamares-settings-debian` are real trixie packages. The KDE task depends on `kde-standard` and `sddm` [R2]. Redundant explicit `sddm` is harmless.
- `config/packages.chroot/` is the documented local-package route [R3]. The desktop package supplies its overlay; an empty `includes.chroot` directory is not a missing-copy bug in that design.
- `config/hooks/live/0990-remove-proxy.hook.chroot` has the documented location/suffix, runs after package/overlay configuration, and includes its required validator package [R4].
- The trixie Calamares settings source points unpackfs at `/run/live/medium/live/filesystem.squashfs`, matching the normal Debian live filesystem name. Its install sequence includes `displaymanager`, and its supported-manager list includes SDDM [R5]. Keep the default filesystem path unchanged unless also updating installer configuration.
- The live-build manpage recommends `http_proxy` for HTTP proxying [R1]. Passing that variable into the build process is reasonable. HTTP mirrors avoid an extra CA dependency in the bootstrap target while APT signatures should remain enabled. This does not remove the need to audit resulting image trust/proxy configuration.
- Calamares is supplied with Debian-specific settings, helper scripts and a desktop launcher [R6]. Presence does not establish successful partitioning, bootloader setup, account creation or installed reboot.

## Minimum evidence after the first build

Record final target package versions, ISO checksum and bootloader contents. Confirm both target launchers are executable, Chromium is present, desktop-file validation passed, SDDM is enabled and no build proxy trust was shipped. Then collect actual live desktop captures and perform disposable-disk install/reboot checks. Verify both initial and subsequent logins, user customization persistence, offline LibreOffice launch, and Office browser navigation. Authenticated Office functionality and physical hardware remain separate acceptance checks.

## Primary sources

All accessed 2026-10-23. Exact package/source archives below were read as data only; no archive code was executed.

- [R1] Debian trixie `lb_config(1)`: https://manpages.debian.org/trixie/live-build/lb_config.1.en.html . Exact frontend aliases checked in https://deb.debian.org/debian/pool/main/l/live-build/live-build_20250505+deb13u1_all.deb .
- [R2] Debian trixie KDE task dependencies: https://packages.debian.org/trixie/task-kde-desktop .
- [R3] Debian Live Manual, package installation: https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-package-installation.en.html .
- [R4] Debian Live Manual, contents/hooks: https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-contents.en.html .
- [R5] Exact Debian Calamares source archive: https://deb.debian.org/debian/pool/main/c/calamares-settings-debian/calamares-settings-debian_13.0.13.orig.tar.bz2 ; inspected `calamares/modules/unpackfs.conf`, `calamares/modules/displaymanager.conf`, `calamares/settings.conf` and `calamares/modules/welcome.conf`.
- [R6] Package details and installed file list: https://packages.debian.org/trixie/calamares-settings-debian and https://packages.debian.org/trixie/all/calamares-settings-debian/filelist .
- Debian Live Manual, Debian Installer distinction: https://live-team.pages.debian.net/live-manual/html/live-manual/customizing-installer.en.html .
