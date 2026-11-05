# Binary School project instructions

- Keep all project work inside `binary-school/`. Preserve sibling projects and repository-root files.
- This is a Python standard-library local server plus buildless HTML/CSS/JS. No package installation is needed to run it.
- Keep existing lesson IDs stable so browser progress and deep links survive.
- Every course should retain a downloadable binary flag lab and interactive answer feedback. Larger assignments remain ungraded.
- Label executable architecture and compiler honestly. GCC output must not be described as MSVC output. Native MSVC build scripts need Windows verification.
- Use original standalone teaching and examples. Do not bundle third-party course PDFs, textbook pages, credentials, or personal progress.
- Validate meaningful changes with `python3 -m unittest discover -s tests -v`; for browser logic also run `node tests/test_course.cjs` and `node --check site/app.js` if Node.js is available.
- When changing downloadable binaries or packaged labs, update their relevant checksum manifests and ZIPs.
- The server binds to loopback. Keep setup and limitations documented in README files.
