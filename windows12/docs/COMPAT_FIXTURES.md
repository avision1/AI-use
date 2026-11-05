# Reproducible Windows application QA inputs

`python3 -B scripts/compat-fixtures.py` downloads the four pinned upstream installers in `build/compat-fixtures.lock.json` into ignored `.work/compat/`. `--verify-only` repeats all pin and required signature checks without network; `--list` only prints the lock. No app is run, installed, added to the ISO or registered as a handler. Requires curl and an existing sqv for the Notepad++ publisher check; no host packages are installed.

| Case | Fixed input | Evidence required later |
|---|---|---|
| x64 EXE | 7-Zip26.05 x64 | GUI installation, ZIP/7z creation/extraction, native hash comparison, removal |
| x86 EXE | 7-Zip26.05 x86 | Independent32-bit bottle/runner and functional archive operations |
| MSI | 7-Zip26.05 x64 MSI | Separate installation/use/removal; EXE success is insufficient |
| Editor | Notepad++8.9.8.1 x64 EXE | Edit/save/reopen UTF-8, non-ASCII filenames, clipboard/file chooser, removal |

The lock's sizes and SHA256 match official fixed GitHub release asset metadata, reread2026-11-05:
- https://api.github.com/repos/ip7z/7zip/releases/tags/26.05
- https://api.github.com/repos/notepad-plus-plus/notepad-plus-plus/releases/tags/v8.9.8.1

7-Zip assurance here is official HTTPS metadata plus exact digest/size pins; no publisher signature is claimed. Notepad++ additionally requires its pinned detached binary signature and versioned public key. sqv must return the exact authorized primary certificate fingerprint `14BCE4362749B2B51F8C71226C429F1D8D84F46E`; default cryptographic/time policy remains enabled. Key bytes are SHA256-pinned to the official versioned repository file. This is not a future revocation monitoring service. Source identity: https://github.com/notepad-plus-plus/notepad-plus-plus/blob/v8.9.8.1/nppGpgPub.asc .

Paths, schemes, upstream repositories, duplicate names, sizes and hashes are checked before downloads. Existing cached mismatches fail; they are never silently replaced. Partial downloads have unique contained names and remain for diagnosis. Verification records are atomically replaced only inside the project. No installer is given executable permissions by the script. `verification.json` explicitly keeps application execution/compatibility false; publisher signatures are not asserted for all inputs.

## Measured on2026-11-05
All four real assets downloaded, exact lengths/SHA256 passed. Notepad++ detached signature verified with the pinned primary fingerprint using existing host sqv. Offline `--verify-only` passed. A copy with one altered byte was rejected by the actual signature verifier (exit1). Reports: `.work/compat/verification.json`, `publisher-negative-check.json`; operational logs `.work/compat-prepare.log`, `.work/compat-publisher-verify.log`, `.work/compat-offline-verify.log`.

No installer, Wine/Bottles runtime, application window or application workflow was executed. The complete runtime/functional acceptance remains in WINDOWS_APP_RUNTIME_PLAN.md. Do not relabel input verification as Windows software support. These fixtures were prepared while the OS builder ran; its frozen source archive was not changed. Binary caches and generated reports are ignored/reproducible; Git stores only the lock, downloader and instructions. If upstream removes bytes, separately preserve checked originals inside project-owned storage; Git alone cannot recover them.
