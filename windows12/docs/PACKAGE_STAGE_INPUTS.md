# Host package-stage preparation

`scripts/package-stage-inputs.py` is a host-side, read-only archive validator for the controller's fixed local HTTP delivery. It does not launch a VM, start a server, fetch anything, install packages, unpack archives, inspect guest files, or authorize a package stage. Controller job exclusion and frozen `checks.tar` byte hashing remain independent requirements.

Load this trusted source with bytecode writing disabled (the controller uses Python `-B`), or compile its source into a module with an absolute `__file__`. There is no command-line entry point and importing the module performs no filesystem operations. Call:

```python
inputs = package_stage_inputs.prepare(ROOT, absolute_manifest_path)
try:
    # Serve inputs.raw_manifest only at /package-plan.json.
    # For a strictly parsed /package-cache/<sha>.deb request:
    payload = inputs.open_payload(sha)
    if payload is not None:
        stream, size = payload
        with stream:
            # Send exactly size bytes through the controller-owned HTTP server.
            pass
    # Keep inputs alive until the VM and delivery server are stopped.
finally:
    inputs.close()
```

`prepare(project: Path, manifest: Path)` requires the canonical module project root and an absolute manifest strictly beneath it. It returns `PreparedInputs` with:

| Attribute/method | Meaning |
| --- | --- |
| `lock_fd` | Open exclusive prefetch-lock descriptor; `None` after close |
| `raw_manifest` | Exact validated manifest bytes, capped at 2 MiB |
| `manifest_sha256` | Lowercase SHA256 of those exact bytes |
| `plan_nonce` | Original planning nonce |
| `packages` | Allowlisted remote SHA256 to `{path: Path, size: int, identity: tuple}` |
| `provenance` | JSON-safe manifest/source hashes, plan nonce, remote entry count, remote bytes and unique cache files verified |
| `open_payload(sha)` | New binary stream and declared size, or `None` for an unlisted hash; fails if closed or changed |
| `close()` | Idempotently close the held lock descriptor |

Do not serialize `packages` directly: it contains local `Path` objects. Copy `provenance` to the controller's run evidence. The controller must enforce request-path parsing and fixed routing, and close every returned stream. The method accepts a bare digest, never a path or URL. Guest import hashes the delivered bytes independently.

## Required evidence and bounds

Preparation refuses aliases and anything except single-link regular metadata/cache files, traversing every directory component with `O_DIRECTORY|O_NOFOLLOW`. Metadata reads are bounded and compare stable stat identities before/after reads and after reopening. JSON rejects duplicate keys and nonfinite numbers. The manifest must identify schema 1, `planning_only: true`, a 32-character lowercase hexadecimal nonce, a full transaction planned with an isolated empty archive cache, and signed-catalog coverage of every remote URI. Remote URI/SHA256 and local input/archive counts must equal their actual list lengths.

The sibling `run.json` must have `package_planning: true`, its `planning_nonce` must match the manifest, and its `source_sha256` must match the fixed `.work/builder/build-source.sha256` file containing exactly 64 lowercase hexadecimal characters plus an optional newline. The sibling `build.exit` must contain return code zero. The preparation module does not rehash `checks.tar`; the controller already owns that frozen archive verification.

The combined remote/local plan is limited to 4,096 entries, 512 MiB per entry and 8 GiB total. Names must be unique safe ASCII `.deb` basenames; Debian epoch `:`, `+`, `%`, and `~` spellings are retained. Conflicting digest sizes fail. Remote entries have exactly the six exporter fields and bounded ASCII package identities. URLs are restricted to the reviewed official Debian archive authorities and pool paths, without credentials, ports, query strings or fragments. Only the prefetch consumer's narrow `+`, `:`, and `~` URL escapes are accepted. URLs are validated evidence only and never opened.

Local archives require the exact size/SHA256 shape, safe immediate config source under `/root/windows12-build/config/packages.chroot` or `/root/windows12-build/config/packages`, and a safe informational target under `/root/windows12-build/chroot/packages`. Each must match exactly one local-build input and regular-file provenance entry. No corresponding host file is opened. The guest importer owns actual guest local-file verification and its narrowly reviewed link-pair exception.

## Cache and lock lifetime

The fixed `.work/package-prefetch` and `cache` directories must already exist safely. Preparation may create only `prefetch.lock`, mode0600, without truncation; it acquires `LOCK_EX|LOCK_NB` immediately and fails if another owner holds it. It never waits, removes a lock, creates cache directories, or touches `status.json`. A previous complete status cannot bypass missing or invalid cache bytes. Failure closes every acquired descriptor and releases the lock.

Every unique remote digest must exist at `.work/package-prefetch/cache/<sha>.deb`. It is opened with `O_RDONLY|O_NOFOLLOW|O_NONBLOCK`, required to be a single-link regular file at the declared size, completely SHA256 hashed, and checked for stable device/inode/mode/owner/link/size/mtime/ctime identity. No cache file is written. A final complete identity pass occurs before return. `open_payload()` reopens the fixed allowlisted cache path and checks its current descriptor against the recorded verified identity, also checking the held lock pathname. The controller must stop its server before `close()` and must not reuse this object for another run. Stat checks detect ordinary replacement/modification; guest byte hashing remains necessary.

Source validation for this implementation was limited to AST parsing and manual contract review. No module import, host test, network activity, VM launch, cache download, or package installation was performed. Complete-cache preparation and local delivery remain runtime gates.
