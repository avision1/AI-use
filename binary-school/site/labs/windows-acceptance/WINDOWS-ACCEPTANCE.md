# Native Windows acceptance

This kit is prepared for a Windows maintainer. It is **not a record of a completed Windows run**. The Linux build host cannot perform native MSVC, x64dbg, WinDbg or Windows screen-reader acceptance. Wine and cross-compilation do not establish that result.

The website needs only Python and a browser. These extra tools are for verifying native practical lessons. No installer, execution-policy change or network service is run by this kit.

## Automated compile and program contracts

1. Open an **x64 Native Tools PowerShell** session with Visual Studio C++ Build Tools and the Windows SDK available. Check `cl.exe` resolves to the intended installation. Run from the project folder:

   ```powershell
   & .\site\labs\windows-acceptance\Verify-Windows.ps1 -Architecture x64
   ```

2. Repeat from an **x86 Native Tools PowerShell** session using `-Architecture x86`. Follow your administrator's normal script policy; do not disable protections to run it.
3. Inspect `.qa/windows-x64/acceptance.json` and `.qa/windows-x86/acceptance.json`. The script builds 76 executables per architecture: guided and optimized versions of 13 course flags, 9 practical/final programs, 7 full-kit programs, 8 casebook pairs and the exception lab. It checks PE machine type and hashes, flag/practical/final behavior, parser failures, and handled exceptions. Full-kit and casebook builds are compile/architecture checks; do not treat them as runtime-contract coverage.
4. Compiler path/version, OS version, flags (build recipe), hashes, stdout and exit codes form reproducible evidence. Reports contain local file paths; inspect them before sharing. The script records `automated-pass-manual-pending`, never a whole-release pass. Build logs and artifacts stay inside `.qa/` under this project.

## x64dbg / x32dbg manual acceptance

Use the guided native MSVC `practical-windows-guided.exe` and its PDB in the corresponding QA folder.

- [ ] Record debugger version, binary hash, architecture and command line `LAB 4`.
- [ ] Reach actual `main` using symbols or string/import references; distinguish it from system/CRT startup.
- [ ] Stop at the call site of `IsDebuggerPresent`; step over it, record EAX and the controlling branch. A debugged run should take DEBUG_PATH and exit3.
- [ ] Restart, change EAX to0 immediately after that API returns, and continue. Explain why this changes only that process. Compare with the normal run's quote28, flag and exit0. PID varies.
- [ ] Stop at the call site of `lstrcmpA`, record both string pointers, and decode `LAB`. Use RCX/RDX on Windows x64; inspect the actual x86 calling convention and stack in x32dbg.
- [ ] Record a real backed RVA-to-file conversion using section virtual/raw metadata, and one recovered Order field offset.

## WinDbg and first-chance exceptions

Use `windows-exception_lab-guided.exe` with its MSVC PDB. The program raises a bounded custom exception and handles it itself; no file or network behavior is involved.

- [ ] Record WinDbg version. Configure symbols for your QA folder, reload, and verify `main` is visible with `x MODULE!*main*` (substitute the actual module from `lm`).
- [ ] Set `sxe 0xe0421001` and continue. At the **first-chance** stop, record exception code, current instruction, stack and registers.
- [ ] Use `gn` to pass the exception to the application. The handler should print `handled=1` and exit0. Explain why the earlier debugger stop did not establish a crash.
- [ ] In a fresh run compare the debugger's handled/swallowed behavior only for this training exception; record the difference. Do not change global exception or system settings.
- [ ] Repeat relevant symbol/call observations with the other architecture; don't infer x86 behavior from an x64 screenshot.

## Persistent computational repair

- [ ] Keep an original native MSVC `practical-final-cedar-guided.exe` (or quartz/willow) and hash it.
- [ ] Recover `adjustment` and repair its initialized value from1 to9 in a **copy** using Ghidra or your debugger's file-patching workflow. Export the executable and record its new hash.
- [ ] With Python on Windows, run `py -3 site/labs/readiness/verify-repair.py cedar PATH-TO-YOUR-PATCHED-EXE`. It executes your own training file and checks nine quantities plus seven invalid/token/probe cases.
- [ ] Confirm the original still produces original results and that restarting the patched file retains the repaired computation. A source rebuild or register edit is not this check.
- [ ] Preserve reconstructed C, addresses, tested inputs, stdout/exit statuses and any export limitations. The browser exact-byte checker targets supplied MinGW/ELF binaries, not a newly compiled MSVC file; use the behavioral verifier for MSVC.

## Keyboard and assistive technology

- [ ] Test skip-to-content, lesson-to-lesson heading focus, blank fields and feedback, mobile lesson disclosure at narrow width, keyboard backup choose/preview/merge/recovery, and notebook persistence after reload.
- [ ] Test one supported screen reader/browser combination and record actual versions and any announcements that were missing or repeated.

Only mark an item complete after observing it on Windows. Keep missing tools and deviations explicit; do not fill a pass field from this document's expected observations.

Primary references: [x64dbg run/step controls](https://help.x64dbg.com/en/latest/gui/menus/Debug.html), [Microsoft WinDbg user-mode tutorial](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/getting-started-with-windbg), [Microsoft exception-handler syntax](https://learn.microsoft.com/en-us/windows/win32/debug/exception-handler-syntax).
