# Recovery probe and observed limits

This probe checks full-VM reboot/rerun behavior independently of the running OS build. It never uses the main builder disk, QMP controls or HTTP server. Runtime files stay under `.work/recovery-probe/` and `artifacts/recovery-probe/`; the base cloud image and project-local QEMU tools are read only.

## Commands

Run from the existing `AI-use/windows12/` directory, once each, in separate tool invocations so the infrastructure proxy environment can change:

```bash
python3 -B scripts/recovery-probe.py --phase 1 --timeout 300
python3 -B scripts/recovery-probe.py --phase 2 --timeout 300
```

Each invocation runs at most one QEMU TCG guest with one vCPU and 1 GiB RAM. It uses `smm=off`, a new project-contained 4 GiB virtual qcow2 backed by the already checksum-verified cloud image, no host filesystem share or block device, a dedicated local HTTP endpoint on port 8767, and phase-specific QMP FIFOs. A nonblocking runner lock rejects concurrent probe invocations. Existing phase output is never overwritten. Preserve both owned work/output directories before deliberately starting a new probe sequence.

Phase 1 boots the frozen guest Python payload, increments a guest disk counter, sends a validated callback and powers off. Phase 2 reuses that exact virtual disk and payload digest while changing NoCloud instance-id, runtime token and proxy environment. A successful callback must show counter 2, the new token/proxy value, the original payload digest, and a clean VM exit. Process startup or an exit code alone cannot pass the check.

The identifier stays `nocloud-net` across both boots. It is currently deprecated upstream, but changing datasource identifiers during a recovery trial confounds the experiment. Migration to `nocloud` needs separate validation.

## Actual observations — 2026-10-23 America/Chicago

Phase 1 passed in a real Debian guest:

- Frozen payload SHA256: `39f689cd732a6a19386cf378a001f7068d5020df69caf87f2ebf7fb64fb46c11`.
- Guest persistent counter: 1.
- Reported translated proxy environment: `http://10.0.2.2:34809`.
- Exact phase token/source callback accepted with HTTP 201; QEMU powered off with exit 0.
- `artifacts/recovery-probe/phase-1/result.json` contains the command and verified result.

Phase 2 also passed in a separate tool invocation using the same qcow2:

- Guest persistent counter advanced to 2.
- Payload digest stayed exactly the same.
- New phase token was accepted; reported proxy environment changed to `http://10.0.2.2:40001`.
- NoCloud metadata, user-data, vendor-data and network-config were fetched again with HTTP 200, followed by callback HTTP 201.
- QEMU powered off with exit 0; `artifacts/recovery-probe/phase-2/result.json` records `verified: true`.

Both probe jobs are stopped. Phase 1 used session 35102 and phase 2 used session 34341; neither is a running job to resume. Their owned virtual disk remains under `.work/recovery-probe/probe.qcow2`, and full logs/callbacks/results remain under `artifacts/recovery-probe/phase-1/` and `phase-2/`.

After the runtime proof, source-path hardening added support for either the verified legacy cloud cache filename or the dated filename from the immutable lock, and refusal of probe disk/owned-root symlinks. These host-side portability/containment changes were reviewed without another VM run; the frozen guest payload and its measured digest are unchanged.

The phase-1 serial log stopped around early kernel `/init` output, although later NoCloud HTTP requests, a successful guest callback and clean poweroff proved real userspace execution. **Serial silence alone does not establish a hung guest.** Use HTTP request/exit evidence and QMP status together. This explains why a recovery diagnosis based only on absent serial progress can be inconclusive.

## What this does not prove

The probe establishes successful frozen-payload rerun with refreshed metadata/environment on the preserved guest disk. It does not establish successful interruption/resume of a live-build package-install or image-construction stage. It does not exercise Microsoft services, physical installation, a target desktop or host package installation. It checks whether a frozen guest task can rerun on the preserved disk with refreshed metadata and environment. The live-build recipe must still reconcile its own partial stage state safely.
