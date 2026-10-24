# Interactive contained desktop validation

W12-020 owner: `/root/desktop_audit`. Status: source implemented; AST/static review passed, runtime execution pending parent review and a real ISO. No desktop success is claimed. Owned files are this document and `scripts/desktop-test.py` only. Every writable directory remains within `/workspace/scratch/3c38ab731138/AI-use/windows12/`. Parent owns integration and commits.

The harness reuses the reviewed containment, shared runner lock and single-client QMP helpers from `boot-test.py` via `runpy`. It requires a real, existing project ISO, a new output directory, and optionally one new disposable VM disk. No current builder, host device, host mount, existing disk or shared host directory may be used. Static review must complete before parent authorizes any VM execution.

## Start one owned guest

Only after the existing builder has stopped, from `AI-use/windows12`, launch in a **TTY-backed** tool session:

```sh
python3 -B scripts/desktop-test.py artifacts/vm-build/windows12-amd64-preview.iso --output artifacts/desktop-review-001 --timeout 1800
```

The existing authenticated project QEMU/SeaBIOS toolset must be prepared already. The harness uses software emulation, `pc,accel=tcg,smm=off`, two virtual CPUs, 4096 MiB default memory, explicit VGA and an emulated USB tablet for absolute pointing. No host GPU, USB device or physical block device is attached. The ISO is read-only and its SHA256 is recorded. BIOS testing does not certify UEFI or Secure Boot.

Optional flags:

- `--disk-size 24G` creates a **new** `disposable-install.qcow2` within the new output directory. Sizes8G–128G are accepted; existing disks are never accepted. The disk is retained after shutdown. This does not automate or certify installation, and this version cannot boot an existing installed disk.
- `--network user` explicitly enables QEMU user-mode NAT with one emulated NIC. Default is `--network none`. There are no forwards, host filesystem shares, clipboard or authentication integration. NAT does not import this environment's managed proxy or CA configuration, so Internet access may still fail in a restricted environment. Never disable TLS checks to make a web test pass.
- `--memory` accepts1024–8192MiB. `--timeout` accepts1–7200seconds, default1800. The guest-session deadline includes QMP handshake and interaction; cleanup has additional bounded QMP/process waits. Initial ISO hashing occurs before the guest starts.

All paths are checked before output creation. Internal symlink aliases, escaping paths, existing output directories/files, invalid ISO signature, missing tools and non-TTY input are refused. At least1GiB free is required without a disk,8GiB with a new disk. Screenshots additionally require512MiB free; these are conservative starting guards, not storage reservation. The shared builder `runner.lock` is held for the whole session and cleanup; live/ambiguous legacy QMP controls also refuse a launch. Do not run other project VMs concurrently.

## Operate through the existing TTY handle

Send newline-terminated commands to that harness's supervising tool handle; do not attach another QMP client. An initial screenshot is collected after handshake.

| Command | Behavior |
|---|---|
| `screenshot` or `shot` | Save the next `screen-NNNN.ppm`, validate its P6 pixels and print its absolute path/dimensions. Inspect that actual image before choosing UI actions. |
| `status` | Print the owned emulator's QMP status. Running is not evidence of a usable guest. |
| `keys ctrl+alt+t` | Send one chord,1–8 distinct supported QEMU qcodes joined with `+`. Examples: `keys ret`, `keys alt+f2`, `keys meta_l`, `keys ctrl+l`. There is no arbitrary QMP/HMP or host shell command interface. |
| `text Public test document` | Type1–256 printable ASCII characters using a fixed US keyboard mapping. Leading/trailing payload spaces are preserved. Enter/newline is separate: `keys ret`. Verify a simple disposable echo field first; layout, Caps Lock and TCG timing can affect text. Unicode/non-US input is not implemented. |
| `click 120 240` | Click a pixel coordinate with the left button; optional final token `left`, `middle` or `right`. A fresh screenshot is retained first. Coordinates must fit that framebuffer, and a changed display size rejects the click so the new image can be reviewed. Coordinates map to QMP absolute range0–32767 through the USB tablet. |
| `help` | Print the fixed command summary. |
| `stop` | End interaction and stop only the guest created by this process. Its optional disposable disk and evidence remain. |

To open a selected file reliably, use a reviewed `click` followed by `keys ret`. Two `click` commands may produce a double-click, but their intervening safety captures can exceed the guest's double-click interval; no timing success is promised. A screenshot also does not prove that a target remained unchanged. A terminal inside the guest can be operated using these same input methods, but no command is executed by a host shell. Do not use UI automation to select physical devices: the guest exposes only its read-only ISO and optional new disk.

**Public disposable data only.** Command logs redact key/text payloads, but screenshots show guest contents and the TTY may echo input. This harness provides no private credential entry, secret redaction, secure login handoff or authenticated Microsoft account testing. Do not type real passwords, tokens, personal documents or other private material. Authenticated Office acceptance requires a separate suitable human-controlled workflow; unauthenticated landing pages are not a substitute.

## Evidence and termination

- `run.json`: immutable startup provenance, PID, exact QEMU command, ISO hash, network mode, timeout and new-disk path.
- `commands.jsonl`: accepted/rejected command metadata and input payload lengths/counts, with text/key payloads redacted.
- `qmp-events.jsonl`: replies and events observed by the sole reused QMP client. The helper records responses, not typed request arguments.
- `screen-NNNN.ppm`: retained binary framebuffer captures, including the extra safety capture before clicks. QEMU's P6/255 header, dimensions and exact pixel length are checked.
- `serial.log`, `qemu.log`, `qemu-debug.log`: guest/emulator diagnostics. A live ISO may have no serial console; silence is not a failure or success.
- `result.json`: termination outcome, captures, QEMU return code and errors. Setup failures after output creation also retain a result. `boot_verified`, `login_verified`, `install_verified` and `workflows_verified` remain **false**; a reviewer must create separate evidence-based validation results.

`stop`, stdin EOF, Ctrl+C, deadline and failures all enter owned-process cleanup. QMP quit is attempted first, then bounded terminate/kill fallbacks on the stored `Popen` object; no name-based process killing occurs. The lock remains held until cleanup and result writing finish. An external kill or environment teardown can bypass this controller: inspect recorded PID/command, lock/QMP state and evidence before another run. Do not reuse the output directory or assume an unknown tool handle means termination.

Exit0 means the interaction ended normally or the emulator exited0, not that any workflow passed. Timeout returns124, interrupt130 and caught failures1. `-no-reboot` means a guest reboot request can end this emulator rather than starting a second boot; record that distinction. Installation acceptance still needs an ISO-free installed-disk boot through a separately reviewed path.

## Review and validation status

AST syntax parsing and source review completed. No harness import, test suite, QMP request, emulator, server, package preparation or actual ISO boot was performed for this implementation. Required next validation: parent reviews source; after a real ISO exists and the builder stops, launch one session, inspect firmware/boot captures, exercise screenshot/status, verify US text/chord input and absolute click accuracy on harmless UI, then perform the desktop gates in `DESKTOP_AUDIT.md`/`VALIDATION.md`. Retain exact failures rather than changing flags to claim success.

QMP interfaces and qcodes were checked against official primary documentation: [QEMU QMP reference, send-key and input events](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-send-key), [input-send-event](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-input-send-event), and [QKeyCode enumeration](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#enum-qkeycode). The documentation defines simultaneous key arrays and absolute coordinates0–0x7fff; actual input behavior with the project's QEMU8.2 toolset remains a runtime gate. Attempts to retrieve the exact v8.2 source through web URLs were unavailable, so no claim of source-level version certification is made.
