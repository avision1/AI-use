# Observed validation — 2026-10-23 America/Chicago

Build attempt 04, contained QEMU TCG Debian13 builder, source tar SHA256 `dd2117c593f8c1ecf1210e0410acbc3004c36d5e56e9832a10df401986376612`.

| Check | Actual result |
|---|---|
| Authenticated project-local QEMU package download/extraction | Passed Ubuntu InRelease signature, package-index and package SHA256 checks; no global installation |
| Diskless QEMU process | Ran for10 seconds; firmware-only result |
| Default SMM guest boot | Failed: stuck BIOS SMM; preserved diagnostic logs/disks |
| TCG smm=off Debian cloud boot | Passed: Linux, systemd, cloud-init and real userspace executed |
| 9p artifact share | Failed: genericcloud lacks9p filesystem; replaced with HTTP exports |
| Overlay unit tests inside guest | **17 passed**, reported `Ran 17 tests in 0.192s`, `OK` |
| Deterministic desktop packaging inside guest | Two builds produced the same7036-byte .deb, SHA256 `eef6eb901577b2694e44965eaf2a0fe687acf954c45f7feb5777b120a4470b8f` |
| dpkg-deb package parser | --info and --contents completed successfully; expected source files/modes listed |
| Guest apt HTTPS | Certificate validation failed against environment proxy; investigating transient guest-only CA trust, no TLS bypass |
| Full ISO build | Not completed |
| BIOS/UEFI live desktop, installation and installed reboot | Not performed |
| Authenticated Office, Wine apps or physical hardware | Not performed |

Primary execution evidence remains under ignored `artifacts/vm-build/serial.log`, guest-build.log when exported, and run.json. This compact record preserves the observed results in Git; it is not a substitute for full release logs or artifacts. The browser calls in unit tests were mocked, so those results establish launcher behavior only. The booted builder cloud OS is not the target distribution.

Follow-up fresh attempt05: public infrastructure CA injection fixed guest HTTPS certificate verification; Debian InRelease and package indexes downloaded with TLS verification enabled. Target ISO still not built at this checkpoint. HTTP artifact export from prior failed build succeeded, including .deb/checksum/log and nonzero exit marker; host .deb checksum matches guest. Experimental resume attempt was inconclusive and stopped before a fresh build.

Attempt06 (24GiB/cache disabled): repeated17 launcher tests and deterministic package gate passed; early desktop artifact export returned201. live-build configured trixie/amd64 and entered bootstrap_debootstrap; a valid Debian Release signature was reported. ISO construction remains running, not a completed image or target boot result.
