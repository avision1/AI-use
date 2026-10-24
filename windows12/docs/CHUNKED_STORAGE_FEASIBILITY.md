# Chunked userspace storage feasibility

Research only, 2026-10-24. **Unimplemented and untested. The current build is unchanged.** This is a conditional response to the observed workspace-copy problem, not a distribution requirement.

## Recommendation

Prototype only if synchronization storage prevents the existing build from finishing. Prefer a maintained NBD server with a split-file backend over writing a new NBD protocol or qcow2 implementation. The official `nbdkit split` plugin already exposes an ordered list of plain files as one disk. Its files must retain their sizes; it lacks trim hole punching and efficient zero writes, and is less efficient than its single-file counterpart. [1]

QEMU supports NBD directly, including Unix sockets. Therefore this architecture does not require `/dev/nbd`, a kernel module, a host mount or a host block device. Merely exporting the existing huge qcow2 through `qemu-nbd` would leave the huge changing file in place and would not address that suspected copy mechanism. QEMU's server normally exports guest-visible image contents, not a chunked persistence scheme. [2][3]

**Inference, not a demonstrated fix:** limiting each mutable file to a small chunk could reduce the size of any individual synchronization copy. The platform might instead copy every changed chunk, retain generations, or copy entire directories. Only measured storage growth can establish improvement. More files can also add overhead and worsen synchronization behavior.

## Smallest useful architecture

Use a separate, new project-contained backend directory, a fixed ordered manifest and fixed-size sparse raw chunks; for example, 24 GiB divided into 16 MiB chunks is 1,536 files. That size is a prototype parameter, not a selected production value. Precreate the complete chunk set and manifest before exposing storage, so normal guest writes do not require a mutable allocation map or new filenames. Missing, wrong-sized, reordered or symlinked chunks must cause startup failure; a missing initialized chunk must never silently become zeros.

Run authenticated, locally extracted nbdkit plus its split plugin in the foreground. Give it only those reviewed regular files, an explicit Unix socket inside a private project directory, and project-local stderr/log/PID/cache paths. nbdkit documents Unix sockets, explicit plugin paths and foreground logging; its default network listener/log behavior must not be relied on. [4] QEMU connects as the sole writer and attaches the resulting raw export as its virtio disk. Preserve the common runner lock across both server and VM lifetimes. The server is an additional process whose failure and cleanup require supervision.

The current wrapper instead creates `.work/builder/build.qcow2` with the checked cloud qcow2 as backing and passes that file directly to QEMU. A future raw-chunk path would initialize guest-visible bytes from the **same hash-verified immutable base**, read-only, using QEMU's format decoder while no guest is running. It must explicitly verify the initialized prefix against the base and the remaining capacity as zero, then preserve the original base and its provenance. Raw chunks would contain the initialized disk rather than a qcow2 delta; this costs additional initial storage and loses cheap backing-file reconstruction. Do not split a qcow2's host bytes and present the concatenation as raw guest sectors.

QEMU documents offline conversion/comparison and cautions against modifying active images. An existing NBD target may require skipping target creation with `-n`; a zero-target optimization is valid only when the new target really reads as zero. Exact options must be checked against our pinned QEMU executable during a prototype, rather than copying current master-documentation syntax blindly. [5] No current build disk should be converted, migrated, resized or switched live for this experiment.

## Durability contract and crash behavior

The NBD specification defines a byte-range export independently of how its server stores those bytes. A successful FLUSH must cover previously acknowledged writes; advertised FUA requires persistence before that request's success reply. Features must not be advertised unless implemented. Multiple connections impose additional consistency requirements. [6]

Prototype requirements derived from that contract:

- Use one client/connection initially. Inspect negotiated flush/FUA capabilities and the authenticated backend version; documentation alone does not prove our extracted binary's behavior. Do not enable unsafe caches or ignore flushes.
- Verify data and metadata durability across all chunks touched by a request, including a request crossing a chunk boundary. Persist the initial manifest/file-directory state before launch. Do not claim cross-file write atomicity or persistence for unflushed operations.
- If a custom backend is ever necessary, it must bound ranges and memory, handle short I/O and ENOSPC/EIO, correlate replies correctly, and propagate failures instead of acknowledging lost writes. Implementing those details would be substantially more work than using a maintained server.
- Start without discard/zero optimizations. The split backend does not reclaim holes on trim. Ignoring optional discard can consume more space; it is preferable to inventing unsupported zero/hole semantics. Never reveal old backing bytes after a supposed zero operation. [1]
- Reopen after a crash only with exact manifest/size/base identity checks. Preserve failed state before any contained guest filesystem recovery. Server restart must not imply an automatic guest resume.
- Host `fsync` does not establish that a platform's asynchronous file synchronization produces a coherent multi-file restore point. Preserve a stopped/flushed complete chunk set plus manifest; do not call a synchronized live directory a disk snapshot.

## Acceptance before use for an OS build

1. Resolve the server/plugin dependency closure from authenticated package metadata into the project; record versions, hashes, license information and executable/plugin identity. Availability in the present authenticated repository has not been checked.
2. In a separate contained test environment, exercise boundary-crossing reads/writes, final-sector limits, malformed requests, read-only base protection, short I/O, full storage and server disconnects. Respect the project instruction that runtime test suites run inside a contained VM.
3. Demonstrate acknowledged-write/FLUSH and FUA behavior across forced server interruption and fresh reopen. Verify seeded base bytes and untouched zero capacity. Confirm no external files, sockets, logs or temporary files were written.
4. Boot a disposable test guest, write and flush known data, stop it, reopen the same chunks and verify persistence. No current build VM may be active concurrently. Compare runtime and synchronization-copy growth with the existing backend under a bounded workload.
5. Update monitor/cleanup/recovery/provenance tooling for the new layout. Existing `.build.qcow2.*` cleanup must never be broadened to arbitrary chunk files. Reject promotion if storage remains unbounded or data-integrity tests fail.

This approach is technically plausible, but it moves risk from one changing file to a new storage/process lifecycle. Stable contained storage supplied by the execution environment would have a smaller engineering burden. No claim is made that chunking preserves disks across environment teardown, fixes synchronization, or improves performance.

## Primary sources

[1] nbdkit split plugin, description and limitations: https://libguestfs.org/nbdkit-split-plugin.1.html

[2] QEMU block drivers, NBD access: https://www.qemu.org/docs/master/system/qemu-block-drivers.html#nbd-access

[3] QEMU NBD server: https://www.qemu.org/docs/master/tools/qemu-nbd.html

[4] nbdkit server, Unix socket / foreground / logging / plugin options: https://libguestfs.org/nbdkit.1.html

[5] QEMU image utility, conversion, comparison, existing targets and active-image warning: https://www.qemu.org/docs/master/tools/qemu-img.html

[6] NBD protocol, introduction, write ordering, transmission flags and FLUSH: https://github.com/NetworkBlockDevice/nbd/blob/master/doc/proto.md

Sources accessed through web retrieval on 2026-10-24. They describe upstream interfaces; none certifies this environment or the proposed backend. Direct retrieval of current split-plugin C source failed, so its precise flush implementation was not independently audited here.
