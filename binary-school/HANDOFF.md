# Binary School checkpoint

All project edits stay inside `binary-school/`. Preserve lesson IDs and sibling projects. The runtime remains Python standard library + buildless HTML/CSS/JS.

## Completed

- High-priority fixes merged through PR #1: autosaving notes, setup first, separate progress evidence, deeper practicals and fresh mock-final variants.
- Medium-priority backup-import safety: previews, merge/confirmed replacement, pre-import recovery/download, legacy validation, and failure handling.
- Required checks pass: 11 Python tests, course UI regressions, new import regressions, and JavaScript syntax.

## Pause and next decision

The user requested a fresh, syllabus-only subagent review while medium-priority work proceeded. The review has returned; finish and push the backup-import fix, show the independent findings, and ask the user for next steps before starting another issue.

Fresh review examined main `a6af0361453632e87e983d505b552dd446b141d2`, before backup-import changes. It raised Windows/MSVC live verification and a prerequisite diagnostic with separate foundation/revision routes as high priorities. It also found contradictory platform wording, incomplete catalog search, mismatched debugger videos, an incomplete syllabus outcome/deliverable map, and an incomplete AI-policy summary. These review findings have not been implemented in this checkpoint. Earlier accessibility work also remains pending.

## Verification limits

Linux binary behavior and automated frontend/HTTP checks were tested. Native Windows/MSVC workflows and rendered browser/keyboard/mobile behavior remain unverified. Supplied Windows PE files are MinGW GCC output; native MSVC builds require the included Windows scripts.
