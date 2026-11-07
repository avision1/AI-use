# Windows12 Linux project

## Current status — complete local removal requested

The user requested removal of the entire local Windows12 working directory, VM disks, ISO, tools, caches and temporary files, while retaining the global continue skill. This supersedes every older instruction below about retained local disks or resuming `clockfix-001`. Source is preserved on GitHub main; the preview ISO, 614 selected evidence/input files, frozen source snapshots and unapplied drafts are archived in the GitHub draft release `windows12-local-archive-20261106`. See `docs/LOCAL_REMOVAL.md`. After verified upload and cleanup, no local VM continuation is available; rebuild in a new contained environment. Shared parent Git metadata is retained to preserve unrelated repository history.


An independent installable Linux distribution project for everyday Windows-style workflows. The first implementation targets Debian 13 amd64 and KDE Plasma, with a familiar taskbar, file manager, settings, Office web launchers and an offline office alternative. It is not a Microsoft product.

**Development status:** a real hybrid preview ISO has passed a content audit, offline BIOS installation through Debian Installer and Calamares, and installed-disk boots without the ISO. Reviewed VM evidence includes the default Wayland desktop and basic DOCX/XLSX save/reopen workflows. Normal UEFI live boot also passed; UEFI installation, broader everyday workflows and hardware coverage remain pending. A replacement ISO containing the missing clock-utility fix is being built and must pass its own validation. See [PROJECT_STATE.md](PROJECT_STATE.md), [Calamares evidence](docs/CALAMARES_PREVIEW4.md) and [UEFI evidence](docs/UEFI_PREVIEW4.md). This is a development preview, without Windows application compatibility certification.

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
