# Fast contained overlay checks

`scripts/check-overlay-vm.py` implements W12-023 for the current working-tree overlay. It uses already cached project-local QEMU tools, the cached pinned Debian cloud image and its cached checksum manifest. It never downloads missing inputs or installs packages. Missing inputs fail rather than calling the tool bootstrap or a package manager.

From `windows12/`, after reconciling previous VM ownership:

```sh
python3 -B scripts/check-overlay-vm.py --timeout 600
```

The timeout is configurable from 60 to 1800 seconds. Software emulation is slower than KVM. A timeout is a failed check with retained evidence, not a successful test result.

## Isolation and preservation

The runner holds the existing `.work/builder/runner.lock` for its complete lifetime and refuses an existing legacy QMP listener without sending a command or replacing FIFOs. It does not use, mutate or resume `.work/builder/build.qcow2`, the frozen `checks.tar`, source lock or previous exit markers. The cached cloud base is SHA512 checked against the pinned image lock and checksum manifest before a new writable child disk is created. Base identity is checked again after a successful run. This retains the existing cloud-image assurance limit: HTTPS/checksum pinning, without a detached signature.

A new private `artifacts/overlay-check-<nonce>/` contains the disposable child disk, source archive, environment directories and output. Host subprocess HOME, TMPDIR and XDG directories point there. Guest root paths and package construction are inside that disk; no host mounts, block devices or filesystem shares are passed to QEMU. Symlink ancestors and unsupported source file types are refused. The main build and tests cannot run concurrently through the shared lock.

The source snapshot covers current `image/`, `tests/`, `scripts/` and `build/`, separately from the retained ISO builder's frozen source. Input reads refuse multiple links and changing files. Each file and the full archive are hashed into `run.json`. Wait for agents/editors to finish before invoking it: per-file stable reads do not make concurrent multi-file editing an atomic project revision.

## Local seed and guest checks

An ephemeral loopback HTTP server exposes only fixed cloud-init seed paths and `/source.tar`. Guest uploads are restricted to `checks.log` (4 MiB) and `result.json` (16 KiB), exclusively created once under the new output directory. Requests have bounded lengths and upload timeouts. There is no arbitrary upload path or package download route.

The supplied guest network configuration uses an on-link static address with no default route or nameserver. Before reading source or running tests, the guest also removes any IPv4/IPv6 default route and verifies both are absent. Initial cloud-init seed discovery may use cloud networking before that point; this is not a certification of hypervisor-level network isolation. All requested guest traffic is to the local seed/source/result server, and the helper contains no package-download commands. This path does not retry or bypass the blocked Debian package origin.

Inside the fresh VM, the helper verifies the source archive digest, extracts it using the safe data filter, runs the overlay unittest suite, builds the desktop package twice and compares bytes, then uses native guest `dpkg-deb --info` and `--contents`. No package is installed. Each child command has a 180-second timeout; unit and package command output is retained in the bounded guest check log. QEMU has the overall host timeout, and only that owned QEMU process is terminated/reaped on timeout or interruption.

## Evidence and limits

Success requires fresh nonce/source hashes, all guest check booleans, no default routes before checks, deterministic package bytes, package digest/size, native inspection success and the exported log's SHA256. `host-result.json` records host completion/error and owned-QEMU termination. Missing, truncated, oversized, stale or unsuccessful guest proof fails. The child disk and all evidence are preserved for diagnosis; no automatic disk cleanup is performed.

This measures unit behavior and package construction for the captured source. Browser actions are mocked by the tests. It does not prove Plasma GUI behavior, Wine/Bottles execution, application compatibility, an ISO build, boot or installation. `iso_verified` stays false. The source implementation and generated guest Python passed AST parsing; the author did not launch a VM or execute project tests. Parent runtime results must be recorded separately.

Runtime refinement: route queries use `show table all exact 0.0.0.0/0` / `show table all exact ::/0` and remove only forwarding defaults by their measured gateway/device/metric/table. IPv6 unreachable/blackhole/prohibit rows do not forward traffic and are retained rather than attempting to flush immutable kernel rows. Per-family before/after route evidence is recorded; successful proof means no forwarding defaults, not an empty routing table.

## Actual runtime result
Third run35105 completed0 at artifacts/overlay-check-6c5d49ef8e31a0e6f59f2303c4b5f1c7:31 unittest cases, deterministic9950-byte preview3 package and dpkg inspection passed; nonce/source/log proofs matched and QEMU stopped. Package SHA256864088a1111468d49a17d5e28d16534b7e013a975795cd3acfb0b09c3dd2beb9. Real route evidence showed two forwarding IPv6 RA defaults, removed by measured gateway/device/metric selectors. Initial unreachable-route explanation was a hypothesis, not the observed final route identity. Neither tests nor this disposable cloud VM establish target GUI or ISO boot/install success.
