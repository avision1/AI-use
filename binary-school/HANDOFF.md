# Binary School handoff

## Scope and authorization

The user requested completion of all previously discussed tasks, regular commits/pushes, and independent subagent reviews. All repository edits must remain inside `binary-school/`; preserve sibling projects, root files, existing lesson IDs and personal progress. Runtime remains Python standard library plus buildless HTML/CSS/JS. No further permission gate is required for authorized implementation work.

## Completed

- PR #1: autosave, setup-first order, separate evidence tracking, deeper practicals, fresh mock finals and computational patch validation.
- PR #2: non-destructive backup preview, merge/confirmed replacement and recovery.
- PR #3: prerequisite diagnostic, foundation/revision paths, weekly evidence/prerequisite map, search, platform wording and full syllabus AI policy.
- PR #4: keyboard/mobile navigation structure, heading focus, skip link, labeled progress and keyboard backup chooser.
- PR #5: malformed startup progress recovery, original-text preservation and truthful save-failure feedback/export controls.
- PR #6: source-free GDB routes, scoped metadata-verified video library, original Windows walkthroughs/diagram, handled-exception lab, separate PDB paths and native Windows acceptance kit.
- Final polish: neutral command/listing disclosure label, verification record and desktop screenshot. The latest independent review found no release-blocking frontend error or critical syllabus contradiction.

## Acceptance status

See `VERIFICATION.md` for actual completed checks and limitations. Eleven Python tests and all six Node suites pass. Supported desktop-browser checks now pass; earlier unsupported-loopback preview failures are superseded. Native Windows/MSVC/debugger execution remains pending because this environment has no Windows runner. Live GDB inferior tracing is blocked by ptrace policy, while static disassembly works. No security settings were changed.

Do not claim Windows acceptance from expected observations or cross-compilation. On an available Windows host, run `site/labs/windows-acceptance/Verify-Windows.ps1` in matching x86/x64 Native Tools sessions and complete its manual checklist. Reports stay in ignored `.qa/` within this project. Screen-reader/mobile-device acceptance also remains pending.

## Maintenance

Run `python3 -m unittest discover -s tests -v`, every `tests/test_*.cjs`, and `node --check site/app.js`. Refresh integrity manifests with `python3 tools/update_checksums.py`; add `--packages` for flag/full/Windows acceptance pack changes. Readiness kit packages use `tools/package_readiness.py`. Keep source and compiler/architecture labels honest; never bundle professor PDFs or textbook pages.
