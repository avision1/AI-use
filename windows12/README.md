# Windows12 Linux project

An independent installable Linux distribution project for everyday Windows-style workflows. The first implementation targets Debian 13 amd64 and KDE Plasma, with a familiar taskbar, file manager, settings, Office web launchers and an offline office alternative. It is not a Microsoft product.

The `clockfix-003` preview passes the content audit, BIOS and normal UEFI Calamares installation, and installed-disk boot without the ISO. It set the hardware clock in both installers. The BIOS VM also passed software updates, file recovery, document reopening and reboot persistence. The live ISO booted with Secure Boot enforced in enrolled OVMF. Preview5 adds a taskbar shortcut to the offline guide and passed the contained source checks. Its ISO build, installed Secure Boot and target-device testing remain open. See [the daily-drive evidence](HANDOFF.md#daily-drive-validation--2026-11-20) and [project state](PROJECT_STATE.md).

## Start or resume engineering

Read [AGENTS.md](AGENTS.md), [HANDOFF.md](HANDOFF.md) and [RUNBOOK.md](RUNBOOK.md). All project writes—including VM disks, caches, downloaded dependencies, temporary files and build logs—must stay within this `windows12/` folder. Only ordinary repository Git metadata is excepted. Never run the target installer or package installation against the host.

The build approach uses a contained QEMU VM, with authenticated dependencies extracted locally. Software emulation remains the default; explicit KVM profiles use only an already available device and perform no host setup. Guest writes stay in project-contained virtual disks and allowlisted local HTTP artifact exports. Fresh candidate paths preserve previous images and frozen source. No fallback to privileged host chroot or global package installation is permitted.

## Source map

| Path | Purpose |
|---|---|
| `image/` | Target OS filesystem: launchers, desktop entries, defaults, help and original wallpaper |
| `build/` | Guest-only OS build configuration |
| `scripts/` | Contained tool preparation, VM build and desktop packaging |
| `tests/` | Overlay checks run in the contained VM; browsers mocked |
| `docs/ARCHITECTURE.md` | Options, decisions and release gates |
| `docs/COMPATIBILITY.md` | Evidence, limitations and per-feature validation requirements |
| `docs/VALIDATION.md` | Build, desktop, installer and application acceptance procedure |
| `.work/`, `artifacts/` | Ignored generated inputs, VM state, logs and release outputs |

## Compatibility expectations

Office launchers open official Microsoft services in browser app windows where available. They require connectivity and an eligible account; they do not include native Windows Office. LibreOffice is an offline alternative with different behavior. Wine, games, Windows-only drivers, domain management and feature parity require separate implementation and version-specific testing. No universal Windows software support is claimed.

Keep generated multi-gigabyte images out of Git. Release artifacts require checksums, input provenance, licenses and real boot/install results. The source's MIT license does not replace the licenses of Debian packages or grant Microsoft software/service rights.
