# Binary School checkpoint

All work stays inside `binary-school/`; preserve sibling projects and existing lesson IDs. Runtime: Python standard library + buildless HTML/CSS/JS.

## Completed

PR #1: autosaving notes, setup first, separate progress evidence, richer practicals and unfamiliar finals. PR #2: safe backup previews/merge/replacement/recovery.

Current checkpoint: prerequisite diagnostic, foundation and focused syllabus-revision paths, weekly prerequisites/effort/evidence targets, four-outcome matrix, complete syllabus AI-policy summary, expanded instructional/practical search and corrected platform wording. Diagnostic results do not grant lesson credit; path/diagnostic fields survive progress backups.

## Authorized next work

The user authorized taking on the next tasks, with subagents reviewing the website and regular commits/pushes. Accessibility checkpoint completed: skip navigation, route-heading focus, current-page/progress labels, mobile lesson disclosure, keyboard backup chooser, and post-action focus. Structural/focus-flow regressions pass; live assistive-technology QA remains pending. Remaining tasks include accurately scoped video support and native Windows/MSVC validation. Use a fresh syllabus-only reviewer on a pushed checkpoint, finish the active issue, then report findings and ask for next steps.

## Checks and limits

Run all Python tests, `node tests/test_course.cjs`, `node tests/test_import.cjs`, `node tests/test_paths.cjs`, `node tests/test_accessibility.cjs`, and `node --check site/app.js`. Keep checksum manifests current.

Linux binaries and automated HTTP/frontend tests are verified. Live Windows/MSVC and rendered browser/keyboard/mobile behavior remain unverified. Supplied native PE downloads are MinGW GCC, not MSVC output; the native MSVC scripts require Windows.

## Fresh review returned

A fresh syllabus-only reviewer examined main `8a51658ea21d211a44b24db842d7ed27afb881e9`. It found no critical curriculum contradiction. It reported six P2 items: keyboard-inaccessible backup chooser; route focus/skip navigation; source-free GDB instructions incorrectly relying on unavailable C; successful interactions ignoring failed persistence; malformed valid stored JSON preventing startup; native Windows acceptance still unverified. The first two are addressed in the current accessibility checkpoint. Other findings remain pending. Finish/push this issue, report the review and ask the user for next steps before beginning another issue.

## Completion authorization and reliability checkpoint

The user now explicitly requests finishing all previously discussed tasks; this supersedes the earlier pause-and-ask checkpoint. Progress startup recovery and truthful storage-failure feedback are implemented and tested. Continue through source-free GDB teaching, appropriately scoped media/walkthroughs, Windows acceptance tooling, supported browser QA, and a final independent review. Do not claim native Windows execution without actually running it. Keep pushing checkpoints.
