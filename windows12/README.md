# Windows12 Linux project

An independent installable Linux distribution project for everyday Windows-style workflows. The first implementation targets Debian 13 amd64 and KDE Plasma, with a familiar taskbar, file manager, settings, Office web launchers and an offline office alternative. It is not a Microsoft product.

**Development status:** desktop source and build tooling are being implemented. No release ISO, successful installer test, or Windows application compatibility certification is available yet. See [PROJECT_STATE.md](PROJECT_STATE.md) for the current verified state.

## Start or resume engineering

Read [AGENTS.md](AGENTS.md), [HANDOFF.md](HANDOFF.md) and [RUNBOOK.md](RUNBOOK.md). All project writes—including VM disks, caches, downloaded dependencies, temporary files and build logs—must stay within this `windows12/` folder. Only ordinary repository Git metadata is excepted. Never run the target installer or package installation against the host.

The build approach uses a full QEMU software-emulated VM, with dependencies extracted locally. Guest writes stay in a project-contained virtual disk and allowlisted local HTTP artifact exports. The builder must pass its execution probe before an OS build is attempted. No fallback to privileged host chroot or global package installation is permitted.

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
