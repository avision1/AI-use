# Binary School

A self-paced reverse engineering learning site that runs on localhost.

- 137 lessons and activities across 13 modules.
- An interactive downloadable flag lab for each course.
- 26 guided/stripped Linux x64 flag binaries.
- Eight comparative C case studies with Linux x86/x64 binaries, real disassembly, state tables, and MSVC build kits.
- Six deeper practical programs, 34 additional guided/stripped ELF and native Windows PE binaries, and three unfamiliar mock-final variants.
- Ungraded learning assignments, worked solutions, autosaving notes/reports, and browser-local progress.
- Separate checkpoint, flag, practical evidence and self-reported readiness records.
- A prerequisite diagnostic and selectable foundation/syllabus-revision paths with weekly evidence targets.

## Run locally

Requires **Python 3.8+** and a current browser. No extra Python packages or Node.js installation are needed to run the site.

| Platform | Start |
| --- | --- |
| Windows | Double-click `Start-Windows.bat` |
| macOS | Double-click `Start-macOS.command`, or run `sh start.sh` |
| Linux | Run `sh start.sh` |

Open **http://localhost:8765/** and keep the terminal window open. Alternatively run `python3 start.py` or, on Windows, `py -3 start.py`. Ctrl+C stops it.

Lessons, exercises, downloads, flag checks, and patch practice work offline. YouTube videos, Godbolt, and external documentation need internet. Ghidra and debuggers are separate local applications.

## Progress

Progress is stored in the browser for this exact hostname and port. Use **Resources → Export progress / Choose backup to preview** to move between installations, browsers, or laptops. Selecting a backup only previews it. **Merge** combines completion/check records and preserves conflicting notes/reports by appending imported text; **Replace** requires explicit confirmation and uses only the selected backup. Before applying either, the site stores a pre-import recovery snapshot and requests a download of your current progress. **Preview pre-import recovery** lets you inspect and restore that snapshot. Storage/download failures abort the import without changing current progress. Check that the requested download actually saved; browsers can block or prompt for it. Personal progress is not committed to this repository. Existing lesson IDs stay stable across content updates.

## Lab platforms and verification

The site runs on Windows, macOS, and Linux. Included ELF executables require matching Linux x86/x64 execution support; static Ghidra analysis does not require running them. New practical and mock-final downloads include native Windows x64 PE files compiled with MinGW-w64 GCC. These are explicitly **not MSVC output**. Use the supplied MSVC scripts in x86/x64 Native Tools prompts to compile the same C locally with MSVC. No prebuilt MSVC binaries are supplied.

Start with **Your first lab environment**, now first in the learning sequence. It includes Windows, Linux, Intel Mac and Apple Silicon routes and a compile/run/debug smoke test.

The original 26 flag executables were checked for accepted, rejected, and malformed inputs. The comparative x64 examples passed 328 input checks. The x86/32 casebook binaries were checked statically, not executed on the build host. The new Linux practical programs and all three final variants were executed in guided and stripped builds, including 16 behavioral repair checks per final build. New Windows PE architecture/imports and repair-byte locations were checked statically. Native Windows execution, MSVC compilation and live debugger workflows require local verification.

Assignments are ungraded. Flag checks give practice feedback. Certificates are unproctored completion records, not accredited credentials or a grade guarantee.

## Structure

- `site/`: complete frontend, curriculum, and downloadable labs.
- `start.py`: standard-library loopback-only HTTP server.
- `tests/`: server/content tests and optional Node.js UI/flag checks.
- `README.txt`: detailed setup, troubleshooting, portability, and editing instructions.

No frontend build step is required. Edit the files under `site/` and refresh.

## Checks

```sh
python3 -m unittest discover -s tests -v
# Optional maintainer checks when Node.js is installed:
node tests/test_course.cjs
node tests/test_import.cjs
node tests/test_paths.cjs
node tests/test_accessibility.cjs
node tests/test_progress.cjs
node --check site/app.js
```

Keep all changes for this project inside `binary-school/`. Other top-level projects and repository-root files are outside its scope.

## Practical readiness and mock final

Each advanced flag lesson now adds a separate investigation with predictions and an autosaving evidence report. The old scalar flag exercises remain warm-ups. The **Practical readiness** page distinguishes study completion, checkpoint success, flags, behavioral predictions and ungraded evidence for the four syllabus outcomes. Existing progress is retained; old checkpoint results cannot be inferred retrospectively.

Lesson 94 uses a separate challenge-only pack with cedar, quartz and willow variants. Source, answers and a self-review rubric are in a separate post-attempt pack. The browser can validate an exported executable containing only the specified computational data patch; it never executes uploads. A local Python verifier in the review kit can check alternative repairs across quantities and failure cases. These are unproctored study exercises, not secure exams.

Notebook and practical-report drafts save as you type. Storage failures display a message; a failed notebook save also prompts before leaving the page. Browser storage can still be cleared, so continue exporting backups.

Maintainers can rebuild the new binaries with `python3 tools/build_readiness.py` using GCC plus MinGW-w64 GCC/binutils; `--mingw-cc` selects the cross compiler. `python3 tools/package_readiness.py` refreshes their ZIPs and lab checksums without rebuilding. Neither tool nor Node.js is needed by students.

Keyboard support includes a skip link, route-heading focus, current-page labels, a native mobile lesson-list disclosure, and a real button for the backup chooser. Structural/focus-flow regressions pass; live keyboard, screen-reader and mobile visual acceptance remain to be performed.

Malformed stored progress is recovered before the interface starts. The original text is preserved and downloadable from the recovery banner or Resources. If saving fails, results remain available for the current visit and an export control stays visible. Do not close the page before exporting when that warning appears.
