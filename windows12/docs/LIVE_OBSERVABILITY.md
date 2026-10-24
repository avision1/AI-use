# Live console observability without a guest restart

Research and narrow tool implementation, 2026-10-24. **No console backend change, device hotplug or guest-agent command was executed for this work.** Actual runtime results must be recorded separately by the designated builder owner after review.

## Preferred first attempt: change only the UART backend

The current wrapper uses `-serial stdio`, without `mon:stdio` or a mux. QEMU v8.2.0 source explicitly supports serial backend changes: `serial_realize_core()` installs `serial_be_change()`, which rebinds handlers and updates serial parameters. `qmp_chardev_change()` refuses a mux, record/replay or a frontend lacking that callback. It constructs the replacement before detaching the existing backend; callback failure attempts to restore the old attachment. These are source properties, not a guarantee that the currently packaged executable will succeed. [1][2]

A ring buffer avoids a changing host console file and needs no guest agent. It captures **future UART output only**. It cannot recover bytes already sent to the prior backend, make a quiet application emit logs, read the guest's log files, or establish build health.

## Reviewable sequence

Use the existing serialized project QMP client; do not attach an independent FIFO reader. Record all replies under the project and reconcile any QMP error/timeout before another mutation.

1. `python3 -B scripts/probe-qmp.py chardevs` sends `query-chardev`. Save the response and existing launch command. Identify the UART's actual label and original backend. For this wrapper it should be a `serialN` label with `filename: "stdio"`; **do not infer the label from this example**, and never select the QMP pipe backend. Stop if it is a mux or the UART identity is unclear. Record `status` and `blockstats` for context.
2. After parent review of that observed response, invoke `python3 -B scripts/probe-qmp.py console-ringbuf --console-id serial0`, substituting the observed `serialN` label. This sends exactly:

```json
{"execute":"chardev-change","arguments":{"id":"serial0","backend":{"type":"ringbuf","data":{"size":1048576}}}}
```

3. Require a matching successful reply. Query `chardevs` again to confirm the same label now identifies a ringbuf backend. Do not repeat the change command to check it: replacing the ringbuf again creates an empty buffer and discards retained output.
4. `python3 -B scripts/probe-qmp.py console-read --console-id serial0` sends exactly:

```json
{"execute":"ringbuf-read","arguments":{"device":"serial0","size":16384,"format":"base64"}}
```

Decode the response's `return` string as base64, preserve the raw response and decoded bytes, and inspect text with an explicit replacement policy for invalid UTF-8. A read **consumes** those bytes; it is not an idempotent observation. The 1 MiB buffer overwrites its oldest unread bytes if full. A single bounded read can leave additional data pending. Base64 avoids QEMU's documented UTF-8 handling limitations for raw console bytes. [3][4]

The tool restricts `--console-id` to `serial` followed by 1–3 decimal digits, requires it explicitly for both console actions (other actions retain an unused internal `serial0` fallback), and retains the previous safe-path checks, five-second bounded response handling and `qmp-client.lock`. It provides no arbitrary backend/path/input command. The label syntax is not UART identity validation. Existing actions remain unchanged. `console-ringbuf` changes the backend and must not be described as read-only; `console-read` drains only the host-side buffer. Neither sends keyboard input or requests guest CPU/disk/boot changes.

## Failure and rollback

On a precondition/backend-creation error, source indicates the attached old backend is retained; a callback failure attempts restoration. A response timeout is **ambiguous**: query the current chardev state through the same lock instead of blindly resending. UART close/open events and modem-state handling are part of the change, so loss or interruption of console traffic is a real risk. No claim of zero disruption is made.

A deliberate rollback uses `chardev-change` on the **same observed UART ID**, restoring the recorded original backend. For this wrapper's ordinary `-serial stdio`, the source schema permits `{"type":"stdio","data":{"signal":true}}`; `signal` defaults true, but confirm the actual launch options first. No rollback action is implemented in the narrow tool. If a project-local file backend is preferred instead, use an explicit contained filename and append mode; this is a new logging choice, not restoration of stdio. Never truncate the existing serial log. Save unread ring-buffer data before replacing it. Do not remove the busy UART chardev with `chardev-remove`, and do not use stop/reset/powerdown/quit as a console-recovery step. [2][3]

## Guest-agent fallback

Hotplugging a `virtio-serial-pci` controller, a socket chardev and a `virtserialport` named `org.qemu.guest_agent.0` would alter the guest's device topology. It additionally requires an installed/running agent, guest kernel support, usable PCI hotplug and service activation. A private project-contained Unix socket is mandatory; no external listener or host filesystem share is needed. This path has more dependencies than swapping the existing UART backend and is not implemented here.

The exact Debian dated directory was fetched over official HTTPS. It provides a `debian-13-genericcloud-amd64-20261021-2638.json` inventory, not the guessed `.packages` filename. Retrieved JSON SHA256: `03a096dbe66029b09cb218a3146159628352189beb5a72010fc61d52afb54458`. Its top-level keys are `apiVersion`, `items`, `kind`; item 0 has a `data.packages` inventory. A second full-text check confirmed **the exact dated JSON contains no `qemu-guest-agent` string**. Thus this supplementary image inventory supplies no evidence that the agent is preinstalled. It is not a query of the currently running guest, where package state may have changed. No matching Debian service/udev activation evidence was established in this review. Do not claim that hotplug will start an agent automatically. [5]

If investigated later, require exact image package-list evidence, its matching Debian service/udev definitions, then bounded `guest-sync-delimited` and `guest-info` responses before any log retrieval. QGA is a separate protocol, not QMP: its initial synchronization requires a unique token and sentinel handling. Restrict retrieval to intended build logs and read-only operations; filesystem freeze, shutdown, time setting, guest execution and file writes are unnecessary for observation. [6]

## Primary evidence

[1] QEMU v8.2.0 UART implementation, `serial_be_change()` and `serial_realize_core()`: https://raw.githubusercontent.com/qemu/qemu/v8.2.0/hw/char/serial.c (lines 894–935).

[2] QEMU v8.2.0 backend replacement, `qmp_chardev_change()`: https://raw.githubusercontent.com/qemu/qemu/v8.2.0/chardev/char.c (lines 1042–1138).

[3] QEMU v8.2.0 exact QAPI schema: https://raw.githubusercontent.com/qemu/qemu/v8.2.0/qapi/char.json (`query-chardev`, `ChardevStdio`, `ChardevRingbuf`, `ChardevBackend`, `chardev-change`, `ringbuf-read`).

[4] QEMU v8.2.0 ring-buffer overwrite/read semantics: https://raw.githubusercontent.com/qemu/qemu/v8.2.0/chardev/char-ringbuf.c (`ringbuf_chr_write`, `ringbuf_chr_read`, `qmp_ringbuf_read`).

[5] Exact official Debian dated inventory: https://cloud.debian.org/images/cloud/trixie/20261021-2638/debian-13-genericcloud-amd64-20261021-2638.json . SHA512-pinned qcow2 identity remains governed by `build/builder-image.lock.json`; this supplementary JSON was HTTPS-retrieved, not independently signature-verified.

[6] QEMU guest-agent protocol synchronization: https://www.qemu.org/docs/master/interop/qemu-ga-ref.html#command-guest-sync-delimited . Master documentation is supplementary; the console proposal uses exact v8.2.0 source above.

Exact source files and Debian inventory were fetched read-only into command output/memory with project-local writable environment variables. No dependencies were installed or extra files downloaded. Source syntax parsing passed for the changed client; no runtime QMP action or host test suite was run by the implementing agent.
