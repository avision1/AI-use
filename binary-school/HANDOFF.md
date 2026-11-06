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

## Additional browser acceptance checkpoint

Rendered 375/768/1280 CSS-pixel checks found and fixed actual 768px overview overflow. All six key routes fit at all three widths after the fix. Lesson outlines collapse at narrow/tablet widths and respond to Enter. The live patch flow validated a real ELF data patch; pass status survived reload. Its saved explanation was missing from the form, so explanation drafts now restore/autosave and have regression coverage. Six Node suites and Python checks must remain passing.

A native file-chooser event call stalled in the browser tool and expired its tabs; do not claim live browser import acceptance from that attempt. The import suite remains passing. This task does not resolve unavailable native Windows, screen-reader or physical-device acceptance. Preserve those limits.

## Unsaved-progress safeguard checkpoint

Failed storage writes now set a transient unsaved-progress guard, covering final explanation drafts and other records even outside lesson routes. Successful saves/imports clear it. Imports first preserve any original malformed startup text; if that cannot be archived, they leave current progress unchanged. Regression suites cover both cases. The user requested another independent syllabus-only subagent review; it is running against the current source. Finish/push this safeguard before reporting findings; continue resolving concrete issues within authorized scope.
