# Read-only builder disk telemetry

When the build console is quiet, inspect the main contained guest's block I/O counters from `AI-use/windows12`:

```sh
python3 -B scripts/probe-qmp.py blockstats
```

This action sends QMP `query-blockstats` with no arguments. It does not pause, resume, stop, power off, modify or inspect the contents of a guest filesystem. It uses the existing project-local QMP FIFOs, path/symlink checks, five-second response bound and serialized `qmp-client.lock`. Only the current designated observer should invoke it; avoid competing clients or repeated filesystem tool invocations while the VM disk changes. The handshake still negotiates QMP capabilities, as for the existing status action.

The JSON reply is QEMU's unmodified response. Examine each device's `stats` object for fields such as `rd_bytes`, `wr_bytes`, `rd_operations` and `wr_operations`. Compare snapshots from the same running guest/device to detect cumulative read/write progress. Device/node names identify which counters belong to the real qcow2, its backing layer or another attachment; do not sum duplicate layers as if they represented independent guest work.

Increasing write counters establish block activity, not a completed package installation or healthy ISO build. Unchanged counters can mean CPU-heavy work, a paused guest, idle work, a blocked operation or a failure; correlate with `status`, monitored disk allocation, free space and serial/build logs. A QMP response proves that the emulator answered this request, not that the guest application is healthy. No counter value certifies an ISO, desktop boot or installation.

## Validation status

The new action's source maps directly to `query-blockstats` and retains the previous command mappings and client-lock path. AST syntax parsing passed. No runtime QMP request was issued during implementation. The designated running-build owner must collect the actual read-only response before runtime validation is recorded. No host test suite or additional guest is needed for that narrow observation.

## Actual validation

The designated builder owner collected two successful responses from the original running guest73.96s apart, using the new action. Same virtio0 device: wr_bytes increased16,220,160,wr_operations867,flush_operations678; rd_bytes unchanged; failed reads,writes,flushes0 in both. Guest CPU state was running on a separate status query. Snapshots/delta are ignored runtime evidence under `.work/builder/blockstats-{01,02}.json` and `blockstats-delta.json`; durable summary is in docs/RESTORED_BUILD.md. No pause/resume/poweroff command or additional guest was used. This validates the observer, not OS-image completion.

Primary reference checked: [QEMU QMP query-blockstats documentation](https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html#command-query-blockstats). Running binary is the project's authenticated QEMU8.2.2; actual responses, rather than master-doc version assumptions, establish this action's behavior here.
