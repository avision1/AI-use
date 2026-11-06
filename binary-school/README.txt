BINARY SCHOOL — LOCALHOST EDITION 1.3
====================================

QUICK START
-----------
1. Extract the ENTIRE BinarySchool ZIP into a normal folder.
   Do not run the launchers from inside the ZIP viewer.
2. Install Python 3.8 or newer if you do not already have it.
   No pip, npm, account, subscription, or extra Python package is required.
3. Start:
   Windows: double-click Start-Windows.bat
   macOS:   double-click Start-macOS.command
   Linux:   open a terminal in this folder and run: sh start.sh
4. Your browser opens http://localhost:8765/
   If it does not, paste that exact address into your browser.
5. Leave the terminal window open while studying. Ctrl+C stops the server.

Manual startup (works on all three platforms with Python 3):
  python3 start.py
Windows alternative:
  py -3 start.py
No automatic browser opening:
  python3 start.py --no-browser

Python downloads: https://www.python.org/downloads/
On Windows, enable the Python launcher or PATH option during setup.
Some Windows installations use the Store launcher instead; the .bat tries
py -3, python3, then python. Use Python 3, not Python 2.
On Linux, install Python 3 using your distribution package manager.
On macOS, if double-click launch is restricted or executable permissions are
not retained by your unzip tool, open Terminal in this folder and use:
  sh start.sh
You do not need to change operating-system security settings.
Use a current desktop browser such as Firefox, Chrome, Edge, or Safari.
Managed school laptops may require administrator help installing Python.
The laptop must support Python 3.8+ and a modern browser; this is not an
Android/iPad app or a universal executable for arbitrary hardware.

OFFLINE AND ONLINE BEHAVIOR
--------------------------
Works without internet after extracting:
* All 137 written lessons and interactive activities across 13 modules and the syllabus coverage map.
* Fill-in-the-blank questions, checkpoints, worked solutions and self-review.
* Search, notebook, completion tracking, and progress export/import.
* Local downloads of C sources, assembly listings, scripts, Linux binaries,
  and native Windows x64 PE practical/final binaries compiled by MinGW GCC.
* Browser byte editor, executable patch validation, and completion certificate.

Internet is needed for:
* Embedded YouTube lessons and Watch on YouTube links.
* Compiler Explorer / godbolt.org and external documentation.
* Installing or updating Python, Ghidra, GDB, Visual Studio, or other tools.
No video files are bundled, no external font service is required, and no
analytics or account service is part of this local edition.
If a video cannot embed, use its Watch on YouTube link. A creator can change
video availability independently of this package.

SAVE AND MOVE YOUR PROGRESS
--------------------------
Progress lives in your browser's local storage for http://localhost:8765,
NOT in the BinarySchool folder and NOT on a cloud account.
Use the same browser profile, hostname, and port each time.
http://127.0.0.1:8765 is a DIFFERENT browser origin from localhost:8765.
Private/incognito browsing may erase progress when closed. Clearing site data
also removes it. Export backups regularly.

To move from the hosted Binary School or another laptop:
1. On the OLD site/laptop: Resources -> Export progress.
2. Save the downloaded binary-school-progress.json alongside your own backups.
3. On the NEW local site: Resources -> Choose backup to preview.
   Selecting a file does not change progress. Review its entry counts.
4. Choose Merge to combine records and append conflicting notes/reports,
   or explicitly confirm Replace to use only the backup.
5. Applying either stores a recovery snapshot and requests a download of the
   current progress first. Check that the download actually saved.
6. Resources -> Preview pre-import recovery lets you inspect/restore the
   preceding record. Only the most recent snapshot is kept in this browser.
   Import is aborted without changing progress if storage/download requests fail.
7. Confirm that your completed lessons and notebook entries appear.
Existing lesson IDs are preserved. Older 42-lesson backups import into the
expanded curriculum; new lessons start incomplete. Unsupported fields and
unknown lesson IDs are ignored. Files must be valid JSON, no larger than5 MB.
Do not place personal backups in site/ if you do not want them served locally.
The server does not scan or execute progress backups or uploaded binaries.

LOCAL TOOLS AND LAB PLATFORMS
----------------------------
The WEBSITE runs on Windows, macOS, and Linux. Individual lab executables
still have architecture and OS requirements:
* Included GCC ELF executables target Linux x86-64. WSL can run them on a
  supported Windows x64 laptop. macOS cannot run Linux ELF files natively.
  On an older Linux distribution, rebuild from C if the included executable
  requires a newer system C library. Build scripts are included.
* Apple Silicon / ARM Linux can read the written lessons and statically
  analyze x86/x64 binaries, but x86 execution requires a matching VM/emulator
  or suitable remote lab. A native ARM build has different assembly.
* Native MSVC Windows PE files must be built locally using Visual Studio
  Build Tools and a Windows SDK. Sources and x86/x64 build scripts are included.
* Ghidra can analyze the supplied ELF and locally built PE files. GDB, x64dbg,
  WinDbg, and Visual Studio are separate local applications, not browser apps.
* 32-bit GCC assembly listings are supplied. Linked 32-bit C builds require
  additional multilib development files on Linux.
* audit.c unsafe mode intentionally permits invalid reads for local diagnosis.
  Use its safe mode for ordinary input checks and sanitizer mode for diagnosis.

Every course now has an Interactive binary lab. Download a guided binary,
recover its accepted integer and flag, then enter the complete BS{...} flag
on that lesson page. Flags are case-sensitive. This is optional interactive
feedback, not evaluation of the longer learning assignments. The independent
build is optimized and stripped. Both builds produce the same flag.
Sources and worked solutions are available for self-review after an attempt.

Flag pack: site/labs/interactive-flag-labs.zip
Contains 26 Linux x64 ELF executables (two for each course), C sources, and MSVC/Linux
build scripts. No native MSVC binaries are bundled.

Comparative casebook: site/labs/comparative-casebook.zip
Eight original worked C examples each include a Linux x64 executable, a
freestanding Linux x86/32 executable, real disassembly listings, source,
state tables in the lessons, and a native MSVC x86/x64 build script.
Linux x64 behavior was checked for 328 input cases. Linux x86 builds were
checked statically, not executed: the build host lacks IA32 runtime support.
Windows PE binaries must be built with the included MSVC script on Windows;
no GCC output is labeled as MSVC output. See the casebook README.

Get the reconstruction lab pack from Resources, or open:
  site/labs/binary-school-full-labs.zip
Its README has build instructions, executable contracts, and report templates.
The website never executes an uploaded executable. Final byte validation is
performed in browser memory. Local comparison/debugging scripts do execute
your chosen files; inspect those files before running them.

TROUBLESHOOTING
---------------
Port already in use:
  Close your old Binary School terminal first. To choose another port:
    python3 start.py --port 8766
  Changing ports creates a separate progress origin. Import a backup there.

Blank page / curriculum not loading:
  Use the localhost URL, not file:///.../index.html. Verify that site/ is
  beside start.py and the complete ZIP was extracted. Refresh the page.

No browser opens:
  Open http://localhost:8765/ manually. Keep the server window open.

Videos fail offline:
  Expected. Read the written material and use the examples; retry videos online.

Downloads won't execute on Linux:
  Extract the ZIP and use chmod +x filename if permissions were lost. Check
  that the binary is Linux x86-64 and that your platform can execute it.

Lost progress:
  Check hostname, port, browser profile, and private browsing first. Import
  your last exported JSON backup. The course folder does not contain browser
  storage and cannot recover deleted browser data.

FOLDER CONTENTS / EDITING
------------------------
start.py                  Standard-library local HTTP server
Start-Windows.bat         Windows launcher
Start-macOS.command       macOS launcher
start.sh                  Linux/macOS terminal launcher
site/index.html           App shell
site/style.css            Styling with system-font fallbacks
site/app.js               All browser UI and interactions
site/curriculum.json      Complete editable course content
site/labs/                Original practice files and expanded lab pack
tests/test_server.py      Server and content smoke tests
tests/test_course.cjs     Optional Node.js UI/flag checks (Node is not needed to run)
SHA256SUMS.json            Package integrity manifest

No build step is required. Edit the HTML/CSS/JS/JSON and refresh the browser.
Do not rename existing lesson IDs if you want saved progress to keep working.
No Git credentials, deployment metadata, third-party video files, or personal
browser progress are included. This local package is independent of the hosted
site: editing one does not change the other.

VALIDATION AND EDUCATIONAL LIMITS
---------------------------------
The course covers the supplied CSC-428 topic outline with extra foundations
and catalog supplements. It is independent of DSU and is not a grade guarantee.
Some completion is self-reported; checkpoints do not verify tool use or mastery.
Certificates are unproctored completion records, not accredited qualifications.
Windows/MSVC build commands and live Windows debugger steps need verification
on your Windows installation; they were not executed on the Linux build host.

Run the included tests from this folder:
  python3 -m unittest discover -s tests -v
They use temporary loopback servers and do not alter your browser progress.

HIGH-PRIORITY READINESS UPDATE (1.3)
------------------------------------
Start with Your first lab environment before assembly/flag challenges. It now
includes Linux, Windows, Intel Mac and Apple Silicon routes and a local smoke
test. ARM hosts need compatible x86 execution/emulation for supplied binaries.

Notebook and practical evidence reports autosave while typing. Storage failure
is reported in the page; notebook failure also prompts before closing. Export
backups regularly. Import/export includes the new checkpoint/evidence records.

The Practical readiness page separates self-reported completion, correct short
checkpoints, flags, behavioral predictions and ungraded practical evidence.
It does not infer past checkpoint success from older completion-only backups.

Advanced flag lessons now include six deeper investigation programs (guided
then stripped) for xrefs, structs, live state, native Windows APIs, encoded
probes and complete C reconstruction. Windows files are genuine PE x64 built
with MinGW-w64 GCC; they are NOT MSVC output. The original C and build scripts
let Windows users rebuild with MSVC x86/x64 for compiler comparisons.

Lesson94 has a fresh challenge-only pack with three variants. Keep the review
pack closed until after the attempt; it contains source, answers, a rubric and
a local behavioral repair verifier. The browser only compares the specified
exported patch; it never executes uploads. These are ungraded rehearsals.

Verification: new Linux guided/stripped practical behavior and final repairs
were executed. PE architecture/imports were checked statically. Live Windows
execution, MSVC builds, and visual browser QA remain unverified on this host.
