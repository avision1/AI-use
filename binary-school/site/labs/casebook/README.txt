BINARY SCHOOL — ORIGINAL COMPARATIVE CASEBOOK

Eight original C investigations. These examples are independent of third-party
course slides and assignments. Source, real GCC listings, and Linux x86/x64
executables are included. All input integers from -20 through 20 were checked in x64 builds against
independent expected results. The x86 files were format/disassembly checked;
this host cannot execute 32-bit programs, so x86 runtime verification is local. The driver reports result=INTEGER and rejects
malformed/out-of-range input with status 2.

Native Windows/MSVC: use an x86 developer prompt and build-msvc-casebook.bat
for the Windows 32-bit comparisons. Repeat with an x64 prompt if desired.
Windows PE executables and MSVC output must be built locally. We do not
mislabel GCC output as MSVC output; Windows execution was not tested here.

Linux x64 builds use the normal C library. Linux x86 builds use a small
freestanding syscall driver, so they do not require 32-bit glibc to run.
They still require x86 execution support (Linux IA32 compatibility or a suitable
VM/emulator). On ARM, use a suitable x86 VM/emulator for execution.
Use Ghidra static analysis on either architecture without executing the file.

When reading disassembly distinguish exercise from runtime startup. The
Linux x86 syscall driver is a delivery adapter, not a model of Windows APIs
or a requirement to learn kernel programming. Focus on the shared exercise.

Only matching inputs within the stated domain are promised. Compiler versions
and optimization choices can change instructions, addresses, and stack offsets.
Use the included source to build your own native MSVC comparison.

Assignments are ungraded. Predict, inspect, trace, reconstruct, compare, explain.
The per-course flag challenges remain separate interactive practice.
