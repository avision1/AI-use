# Binary School

A self-paced reverse engineering learning site that runs on localhost.

- 137 lessons and activities across 13 modules.
- An interactive downloadable flag lab for each course.
- 26 guided/stripped Linux x64 flag binaries.
- Eight comparative C case studies with Linux x86/x64 binaries, real disassembly, state tables, and MSVC build kits.
- Ungraded learning assignments, worked solutions, notes, and browser-local progress.

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

Progress is stored in the browser for this exact hostname and port. Use **Resources → Export progress / Import backup** to move between installations, browsers, or laptops. Personal progress is not committed to this repository. Existing lesson IDs stay stable across content updates.

## Lab platforms and verification

The site runs on Windows, macOS, and Linux. Included ELF executables require matching Linux x86/x64 execution support; static Ghidra analysis does not require running them. Native Windows PE programs are built locally with the supplied MSVC scripts. No prebuilt MSVC binaries are supplied.

The 26 flag executables were checked for accepted, rejected, and malformed inputs. The comparative x64 examples passed 328 input checks. The x86/32 casebook binaries were checked statically, not executed on the build host. Windows builds and debugger workflows require local verification.

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
node --check site/app.js
```

Keep all changes for this project inside `binary-school/`. Other top-level projects and repository-root files are outside its scope.
