BINARY SCHOOL — INTERACTIVE FLAG LABS

There is one original challenge for each of the 13 courses. Each has a guided
Linux x86-64 executable with symbols and an optimized stripped independent
version. Flags match across both versions and local MSVC builds.

Run: chmod +x COURSE-guided-linux-x64
     ./COURSE-guided-linux-x64 INTEGER
The valid parser range is -100..100. Recover the gate using Ghidra/GDB.
A successful input prints BS{...}. Enter the exact flag in the course's
Interactive binary lab lesson. Wrong input exits 1; malformed input exits 2.
The secure-course challenge checks bounds before accessing an array.

The website checks flag text for immediate practice feedback. Assignments
are ungraded. Source and worked solutions are available for self-review;
this is a learning environment, not a secret exam or credentialing system.

Build Windows PE binaries from an x86 or x64 Native Tools prompt with
build-msvc-flags.bat. Flags are the same; target ABI and executable format
differ. Those Windows builds require local testing; only GCC builds were
compiled and executed on the Linux build host.

On older Linux systems rebuild if your C library is incompatible. On ARM
use an x86-64 Linux VM/emulator for execution; Ghidra static analysis can
still inspect the supplied x86-64 binaries. Compiling natively on ARM will
produce ARM assembly instead.

The full lab pack also contains separate guided reconstruction exercises.
Keep source hidden while attempting a binary-only challenge if desired.

BINARY-ONLY GDB ROUTE
Symbols/debug metadata do not include source text. Without C files use:
  set disassembly-flavor intel
  disassemble /r gate
  break gate
  run 0
  x/6i $pc
  info registers
  stepi
  nexti
Use list/next/info locals only for the optional source-level route after
downloading the matching C and adding its folder using directory in GDB.
For stripped builds recover an address rather than relying on the gate symbol.
Managed containers may forbid ptrace; perform live debugging in a permitted
local training environment. Static disassembly alone is not a dynamic test.
