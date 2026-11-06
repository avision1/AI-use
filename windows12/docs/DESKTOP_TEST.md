# Interactive contained desktop validation

W12-020/W12-022 status: source implemented; live/installed GUI execution requires a real ISO and retained successful installation proof. No desktop success is claimed. Every writable directory stays beneath this `windows12/` project.

The harness reuses containment, the shared runner lock and single-client QMP helpers from `boot-test.py` via `runpy`. It accepts either a real project ISO or a sealed successful `install-test.py` result, plus a new output directory. Installed mode opens the proven baseline read-only and writes a new disposable child. No current builder, host device, host mount or shared host directory is attached.

## Start one owned guest

Only after the existing builder has stopped, from `AI-use/windows12`, launch in a **TTY-backed** tool session:

```sh
python3 -B scripts/desktop-test.py artifacts/vm-build/windows12-amd64-preview.iso --output artifacts/desktop-review-001 --timeout 1800
```

The existing authenticated project QEMU/SeaBIOS toolset must be prepared already. The harness uses software emulation, `pc,accel=tcg,smm=off`, two virtual CPUs, 4096 MiB default memory, explicit VGA and an emulated USB tablet for absolute pointing. No host GPU, USB device or physical block device is attached. The ISO is read-only and its SHA256 is recorded. BIOS testing does not certify UEFI or Secure Boot.

Optional flags:

- `--cpu-profile max|Nehalem` selects one fixed TCG CPU model (default `max`). `--video standard|virtio` selects standard VGA or plain 2D virtio-vga (default `standard`), with the corresponding authenticated project-local VGA ROM. No GL renderer, host GPU, passthrough or arbitrary QEMU fragment is accepted. These diagnostic options apply to both live and installed-child modes and are recorded in provenance. They do not change ISO bytes or imply that any selected combination passed a desktop test. A planned clean-ISO test uses `--cpu-profile Nehalem --video virtio`; review its actual captures before claiming success.

- `--disk-size 24G` creates a **new** `disposable-install.qcow2` within the new live-ISO output directory. Sizes8G–128G are accepted. The disk is retained after shutdown. This does not automate or certify installation; installed mode uses the separate proof-based path below.
- `--network user` explicitly enables QEMU user-mode NAT with one emulated NIC. Default is `--network none`. There are no forwards, host filesystem shares, clipboard or authentication integration. NAT does not import this environment's managed proxy or CA configuration, so Internet access may still fail in a restricted environment. Never disable TLS checks to make a web test pass.
- `--memory` accepts1024–8192MiB. `--timeout` accepts1–7200seconds, default1800. The guest-session deadline includes QMP handshake and interaction; cleanup has additional bounded QMP/process waits. Initial ISO hashing occurs before the guest starts.

All paths are checked before output creation. Internal symlink aliases, escaping paths, existing output directories/files, invalid ISO signature, missing tools and non-TTY input are refused. At least1GiB free is required without a disk,8GiB with a new disk. Screenshots additionally require512MiB free; these are conservative starting guards, not storage reservation. The shared builder `runner.lock` is held for the whole session and cleanup; live/ambiguous legacy QMP controls also refuse a launch. Do not run other project VMs concurrently.

## Inspect an installed desktop without modifying its proven baseline

First complete the contained installation and ISO-free one-shot proof in [INSTALL_TEST.md](INSTALL_TEST.md). Then start a new **TTY-backed** desktop session using that successful run's `result.json`:

```sh
python3 -B scripts/desktop-test.py --installed-result artifacts/install-review-001/result.json --output artifacts/installed-desktop-review-001 --timeout 1800
```

Supply either the live ISO positional argument or `--installed-result`. Installed mode refuses `--disk-size` and never accepts an arbitrary existing disk. The prior result must report successful installer completion, ISO-free disk boot, the disabled one-shot proof service and its reported completion stamp. Its exact single serial token, package version and graphical-target/SDDM/configuration audit must agree with the report and both retained phase commands. Both phase results must have exited0 without timeout. Prior phase PIDs must be absent; a reused or otherwise live PID is conservatively refused. The shared runner guard also refuses an active project VM before source validation or output creation.

The result, phase command records, serial log, original ISO and baseline disk must be regular project-contained files without symlink aliases or multiple hard links. The ISO must still match its recorded SHA256 and the installer block graph. The baseline must match `installed_disk` (`path`, `sha256`, `bytes`, `device`, `inode`, `mtime_ns`) sealed by the current installer controller after shutdown, and match both phase block graphs. Older unsealed results are refused; obtain a new successful installation proof. The baseline must be a clean standalone qcow2 without backing or external-data features. Missing, contradictory, duplicated or ambiguous evidence is refused before creating output or a child.

The controller creates a new `installed-desktop.qcow2` with the proven disk as its backing image. It attaches only this child and an explicitly read-only baseline graph; the baseline's own backing is explicitly disabled. The boot command uses the disk boot order and attaches no ISO, direct kernel or initrd. Network remains off unless `--network user` is explicitly selected. At least8GiB free is required. The baseline's SHA256 and full immutable stat identity are checked again before child creation, immediately before launch and after owned-process cleanup. A change produces a failed `baseline-changed-not-certified` result. Reading can update access time, which is deliberately excluded from the identity. Keep the baseline and its original path with the retained child; the child is not standalone.

Use captures and bounded input below to inspect SDDM, log in using only the public disposable account documented by the installation harness, and exercise the installed desktop gates in [DESKTOP_AUDIT.md](DESKTOP_AUDIT.md). The prior one-shot proof has disabled itself, so this boot can remain at the graphical desktop. A prior configuration proof, successful QMP interaction or screenshot does not certify login, application behavior or overall usability. All new guest verification flags start and remain false pending separately reviewed evidence.

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

To open a selected file reliably, use a reviewed `click` followed by `keys ret`. Two `click` commands may produce a double-click, but their intervening safety captures can exceed the guest's double-click interval; no timing success is promised. A screenshot also does not prove that a target remained unchanged. A terminal inside the guest can be operated using these same input methods, but no command is executed by a host shell. The guest exposes only the selected live-ISO/new-disk or installed-child arrangement; no physical devices are present.

**Public disposable data only.** Command logs redact key/text payloads, but screenshots show guest contents and the TTY may echo input. This harness provides no private credential entry, secret redaction, secure login handoff or authenticated Microsoft account testing. Do not type real passwords, tokens, personal documents or other private material. Authenticated Office acceptance requires a separate suitable human-controlled workflow; unauthenticated landing pages are not a substitute.

## Evidence and termination

- `run.json`: immutable startup provenance, PID, exact QEMU command, source ISO hash, network mode, timeout and new-disk path. Installed mode also records the source result/phase/serial hashes, proof token/configuration, baseline hash/stat identity and new child path. The recorded command shows the actual ISO-free block graph.
- `commands.jsonl`: accepted/rejected command metadata and input payload lengths/counts, with text/key payloads redacted.
- `qmp-events.jsonl`: replies and events observed by the sole reused QMP client. The helper records responses, not typed request arguments.
- `screen-NNNN.ppm`: retained binary framebuffer captures, including the extra safety capture before clicks. QEMU's P6/255 header, dimensions and exact pixel length are checked.
- `serial.log`, `qemu.log`, `qemu-debug.log`: guest/emulator diagnostics. A live ISO may have no serial console; silence is not a failure or success.
- `result.json`: termination outcome, captures, QEMU return code and errors, plus `baseline_unchanged` after installed-mode cleanup. Setup failures after output creation also retain a result. `boot_verified`, `login_verified`, `install_verified` and `workflows_verified` remain **false**; a reviewer must create separate evidence-based validation results. Prior proof is nested in source provenance and does not become a new GUI success claim.

`stop`, stdin EOF, Ctrl+C, deadline and failures all enter owned-process cleanup. QMP quit is attempted first, then bounded terminate/kill fallbacks on the stored `Popen` object; no name-based process killing occurs. The lock remains held until cleanup and result writing finish. An external kill or environment teardown can bypass this controller: inspect recorded PID/command, lock/QMP state and evidence before another run. Do not reuse the output directory or assume an unknown tool handle means termination.

Exit0 means the interaction ended normally or the emulator exited0, not that any workflow passed. Timeout returns124, interrupt130 and caught failures1. `-no-reboot` means a guest reboot request can end this emulator rather than starting a second boot; record that distinction. Installed GUI acceptance still needs reviewed login/application evidence from this ISO-free child boot.

## Review and validation status

The installed-mode suite in `tests/test_installed_desktop.py` skips outside `/run/windows12-build-vm`. It uses project-local synthetic evidence to check producer seal compatibility, tampered/replaced disks, changed ISOs, incomplete and ambiguous proof, source aliases, indirect qcow2 refusal, active runners/PIDs, command construction, child creation and false guest-verification flags. The child creation/session test mocks QEMU and qemu-img; it does not boot a guest or validate a real disk image. Run the suite only in the disposable contained test VM. Real ISO boot, installation, SDDM/login, input accuracy and application workflows remain runtime gates; retain exact failures rather than changing flags to claim success.

QMP interfaces and qcodes were checked against official primary documentation: [QEMU QMP reference, send-key and input events](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-send-key), [input-send-event](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-input-send-event), and [QKeyCode enumeration](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#enum-qkeycode). The documentation defines simultaneous key arrays and absolute coordinates0–0x7fff; actual input behavior with the project's QEMU8.2 toolset remains a runtime gate. Attempts to retrieve the exact v8.2 source through web URLs were unavailable, so no claim of source-level version certification is made.
