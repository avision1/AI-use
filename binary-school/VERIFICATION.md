# Verification record

## Completed in this environment

- All 11 Python tests: local HTTP behavior, boundaries, curriculum/download contracts, real Linux guided/stripped program behavior, unfamiliar finals and persistent repair checks.
- Six Node suites: all 137 lesson renders and 13 flag layers; backup preview/merge/replacement/recovery; study paths and diagnostics; expanded search; accessibility structure/focus flow; malformed progress recovery and truthful storage-failure handling; binary-only teaching/media/native-kit structure.
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
