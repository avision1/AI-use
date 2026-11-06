# Verification record

## Completed in this environment

- All 11 Python tests: local HTTP behavior, boundaries, curriculum/download contracts, real Linux guided/stripped program behavior, unfamiliar finals and persistent repair checks.
- Eight Node suites: all 137 lesson renders and 13 flag layers; backup preview/merge/replacement/recovery; study paths and diagnostics; expanded search; accessibility structure/focus flow; malformed progress recovery and truthful storage-failure handling; binary-only teaching/media/native-kit structure.
- JavaScript syntax, Git whitespace, download ZIP and SHA-256 integrity checks.
- Supported live Chrome preview: home and syllabus/lesson rendering, heading focus after lesson navigation, keyboard skip-to-content without rerouting, section-content search, and notebook text retained after navigation and reload. Desktop overview captured in `docs/desktop-preview.png`.
- All six existing video IDs resolved through YouTube's metadata service with matching titles/authors. Playback and captions were not exhaustively streamed.
- GDB 16.3 statically disassembled the supplied gate without any C source present. An attempted live run was blocked by the host's ptrace policy; no security settings were changed.
- A fresh syllabus-only subagent read all six syllabus pages, ran all test suites and inspected the live preview. It found no critical curriculum contradiction or release-blocking frontend error. Its minor generic listing-label issue was corrected.
- A separate focused reviewer checked the native Windows acceptance kit's quoting, PDB paths, source contracts and claims. The debugger-step order and build-evidence recording findings were corrected.

## Not verified here

- Native Windows/MSVC x86/x64 compilation and execution.
- Live x64dbg/WinDbg observations, first-chance exception handling and persistent MSVC binary repair.
- A full screen-reader acceptance run, mobile-device behavior, or exhaustive execution of every written investigation.

The host is Linux and provides no native Windows runner. Cross-compiled MinGW PE files, source review, expected-output tables and a prepared script do not establish a native Windows pass. The guarded kit at `site/labs/windows-acceptance/` emits automated build/program results and explicitly leaves manual debugger/repair acceptance pending. Its checklist describes the exact remaining observations.

The implementation and teaching fixes are complete; these environment-dependent acceptance checks remain open. Do not convert pending items into pass claims in a release record.

## Additional rendered-browser acceptance

The same-origin viewport fixture in `tools/create_browser_qa.py` exercised the overview, environment lesson, flag lesson, resources, patch practice and study-path pages at 375, 768 and 1280 CSS pixels. It found actual overview overflow at 768px. The narrow-layout breakpoint and grid minimums were corrected; all 18 page/width combinations then fit without document-level horizontal overflow. Lesson outlines defaulted collapsed at 375/768 and expanded at 1280; Enter expanded the 375px outline. Recorded measurements for five detailed routes are in `docs/responsive-measurements.json`; the overview was also measured before and after the fix. This is CSS-viewport evidence, not a physical-mobile-device pass.

A live Chrome run loaded the original 15,952-byte ELF, applied the requested 14-byte output patch, and passed validation with the null terminator and remaining bytes intact. The pass survived reload. That check exposed a missing restored explanation in the form; final explanations now restore and autosave drafts before validation. Reload verified draft persistence. The resulting UI is captured in `docs/patch-acceptance.png`. No uploaded executable was run.

The native file-chooser event test stalled in the browser tool and its tabs expired; import acceptance was not counted as a live-browser pass. Backup preview/merge/replace/recovery remains covered by its passing Node suite. Native Windows, full screen-reader and physical-device acceptance remain open as stated above.

## Unsaved-progress guard regressions

The progress suite verifies a leave-page warning after a failed final-draft save even when no lesson notebook is active, and no warning after a successful retry. Import regressions verify that malformed startup text is archived before an import overwrites the main record, that archive failure aborts the import, and that successful import clears visit-only/unsaved status. These are deterministic browser-logic tests, not a native Windows acceptance run.

## Additional independent syllabus review fixes

A fresh reviewer given only the syllabus reference found four actionable issues: invalid lesson routes could stop navigation, lesson 91 linked the wrong Windows source, large own-exports could exceed the import limit, and lesson 129 omitted its required source downloads. All four now have fixes and regression coverage. Eight Node suites and all 11 Python tests pass. Large backups require confirmation before reading, then retain the normal non-mutating preview and explicit apply flow; storage failures remain truthful.

Live Chrome loaded `#lesson/999`, displayed a focused missing-lesson recovery page, and successfully followed its learning-path link. The corrected lesson 91 rendered the Order investigation with native PE and MSVC source-kit links; see `docs/windows-review-fix.png`. The lesson 129 GCC translation-unit pair compiled and printed `result=28`.

A native file-picker retry selected a synthetic JSON backup but produced no visible preview update in this browser automation session. It is not counted as live import acceptance; the eight passing suites include import, large-import and route-error regressions. A separate environment audit confirmed no native Windows or screen-reader runner.

## Portable student ZIP

Fourteen Python tests and eight Node suites pass. Package tests compare two builds byte-for-byte, check archive execute-mode metadata, verify every extracted checksum, reject stale source checksums without replacing an existing package, and reject output paths outside this project. They start the extracted server from a directory containing spaces with an unrelated working directory and ASCII stdout encoding, then fetch its health endpoint, curriculum, homepage and ELF lab. The ASCII encoding case reproduces the startup issue identified by the independent launcher reviewer; an ASCII banner fixes it. These Linux subprocess checks do not establish native Windows/macOS acceptance.
