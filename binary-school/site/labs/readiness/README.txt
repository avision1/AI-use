BINARY SCHOOL PRACTICAL READINESS LABS
Original investigations: xref, records, trace, windows, protected, reconstruct.
Every program has guided and stripped native Windows x64 PE (MinGW-w64 GCC14)
builds. Portable programs also have GCC Linux x64 ELF builds. The Windows API
investigation deliberately has no Linux ELF substitute. MSVC output is built
locally with build-msvc-readiness.bat in x86/x64 Native Tools prompts.
MSVC and live Windows execution need local verification. PE import tables and
architecture were statically checked; Linux execution was tested.

Fresh final variants cedar/quartz/willow are packaged separately. Start with
mock-final-challenges.zip; open mock-final-review.zip only after the attempt.
Sources are self-review aids, not secret exam material. The website never runs
uploaded programs. All exercises are ungraded; flags/checkpoints give feedback.

Inputs are bounded and programs have no network or file-writing behavior.
On Linux chmod +x the downloaded ELF before execution. On older Linux rebuild
from C if the C runtime is incompatible. ARM hosts need compatible x86 emulation
for execution; Ghidra can statically analyze both ELF and PE without running.

See THIRD-PARTY-NOTICES.txt for MinGW runtime licensing notices.
