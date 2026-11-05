BINARY SCHOOL — LOCAL TRAINING LABS

Prerequisites
Basic C, file navigation, terminal use. Start with Assembly from Zero if needed.
Use only the provided programs or other programs you are authorized to analyze.

Linux / WSL
Install GCC, binutils, GDB, Python 3 with your distribution package manager.
On Debian/Ubuntu: sudo apt install build-essential binutils gdb python3
Run: bash build-linux.sh
Prebuilt Linux x64 O0, O2, stripped executables are included.
After downloading a single executable, chmod +x filename may be needed.
32-bit linked C builds additionally require multilib; the header-free leaf-x86.s
can be generated without a 32-bit C runtime. This pack includes both leaf listings.
Optional sanitized builds require GCC sanitizer runtimes.

Windows / MSVC
Install Visual Studio Build Tools with C++ desktop build tools and Windows SDK.
Open x86 Native Tools Command Prompt, cd to extracted folder, run build-msvc-all.bat.
Repeat from x64 prompt. Distinct msvc-x86 / msvc-x64 folders avoid overwrites.
These are native MSVC builds, not MinGW substitutes. No precompiled MSVC files
are supplied; these Windows build commands have not been executed on the Linux host.
Use x32dbg for x86, x64dbg for x64, or WinDbg / Visual Studio with matching symbols.
Ghidra can statically analyze both ELF and PE regardless of host OS.

Recommended progression
leaf → constructs → calls → records → stripped variants → windows_lab
→ obfuscation / misdirection-gcc → patch_logic repair → optional audit/sanitizer/fuzzing.

Independent work
Try binary-only investigations before reading source or course solutions.
Source is included for calibration and self-review, not as an exam secret.
Compare compiler and optimization variants; exact addresses/assembly vary.

Program contracts
constructs-O0 INTEGER: integer -100..100, prints two visits, sum, switch result.
calls-O0: no arguments; prints simple calls, seven-argument total, factorial.
records-O0: no arguments; prints layout and values.
patch_logic-O0 INTEGER: -10..10. Original fee=3*x+7. Repair target=3*x+9.
obfuscation-O0 INTEGER: -100..100; decodes LAB_OK and computes 3*x+7.
audit-O0 safe|unsafe INDEX: -100..100 accepted by parser; only 0..3 valid indices.
  unsafe deliberately permits invalid reads; use audit-san to diagnose.
windows_lab.exe: Windows-only; prints API information, debug path or score.

Checks
python3 compare.py ORIGINAL RECONSTRUCTED (one integer argument contract)
python3 check_repair.py YOUR_PATCHED_FILE
python3 fuzz_indices.py ./audit-san
These scripts execute your local files; inspect files before running. No uploads
are executed by the website. Browser progress and completion records are local,
unproctored, and not accredited.

Evidence report template
1. File hash, architecture, compiler/build flags if known.
2. Inputs/outputs, hypotheses, addresses and instructions supporting conclusions.
3. Recovered signatures/types/control flow and readable C.
4. Debugger commands, before/after state, patch bytes and rationale.
5. Boundary tests, limitations, and unanswered questions.
