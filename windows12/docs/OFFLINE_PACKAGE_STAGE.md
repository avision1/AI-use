# Guest-only offline package-stage runner

`build/run-package-stage.py` is a controller-invoked guest helper. Its only public build invocation is `/usr/bin/lb chroot`. It does not run installer, binary, source or complete ISO stages. Source review and AST parsing are complete; guest execution, archive import, configuration probe and public chroot completion are **not yet measured** by this document.

The controller must hold the existing runner exclusion lock, boot only the retained checked VM, supply the normal VM marker and fresh boot, allow the runner to preserve its fixed prior top-level reports, and serve the exact authenticated full transaction at the importer's fixed local endpoint. No host execution of this helper is appropriate. It requires root, the canonical `/root/windows12-build` working directory, and single-link root-owned helper bytes at exactly:

- `/root/windows12-inspection.py`
- `/root/windows12-recover.py`
- `/root/windows12-import.py`

The controller invokes the runner with `--nonce` (fresh 32 lowercase hexadecimal characters), `--plan-nonce` (distinct original plan nonce), and `--manifest-sha256`, `--inspection-sha256`, `--recovery-sha256`, `--importer-sha256` (each exactly 64 lowercase hexadecimal characters). It must separately pin and deliver the runner itself. No user-controlled shell command or arbitrary path is accepted.

Before creating its workspace, the runner checks the VM/root/CWD boundary, helper bytes, the exact CF0 status and 144-file/450161-byte/1df checksum metadata, all five saved configuration pins, sixteen completed stages with only the reviewed optional runtime flags, absence of other package/build processes and target mounts, and installed live-build source. The source pins come from the authenticated exact `live-build_20250505+deb13u1.tar.xz`, SHA256 `1aad324e433d6cb6d038193252b74fd0ed1c1e1d7e1c6cf410c8fb09c5225b9e`. Ninety-nine regular source files are pinned, covering the frontend, loader, every loaded shell function and all installed public build scripts. The function loader glob membership must also match. Both native builder `dpkg-query` and installed VERSION must identify `1:20250505+deb13u1` (VERSION omits the epoch).

The runner refuses unreviewed LB/options/loader environments, config/all, architecture/distribution variants, frontend environment files, auto scripts, local live-build overrides and the loader's empty-prefix `/functions` and `/scripts/build.sh` fallbacks. Existing five saved configs are only read; no target APT source, trust or resolver file is edited by the runner. It uses a fresh explicit subprocess environment. Import and recovery execute as separate native guest Python processes, and helper pins are checked again at call boundaries.

## Prior-report lifecycle

A fresh nonce still refuses any existing runner/import/recovery-quarantine/staging nonce directory. The exact CF0/1df pre-install state is required before any report preservation; a previously installed target cannot be replayed. After all source/config/status/process/stage checks, the native version check and exact read-only configuration probe succeed, the runner rechecks the complete preflight and preserves only these existing top-level files:

| Fixed previous file | Maximum bytes |
| --- | ---: |
| `package-cache-import.json` | 33554432 |
| `builder-recovery.json` | 262144 |
| `package-stage-result.json` | 1048576 |
| `package-stage.packages` | 8388608 |

Each must be a bounded, regular, single-link root-owned input with canonical ancestry and no group/world write permission. Prior JSON must be an unambiguous object, and must not carry the new nonce. All candidates are inventoried and hashed before the first move. The exclusive fresh workspace contains a mode0700 `previous/` directory. Each file is rechecked, atomically renamed with Linux `RENAME_NOREPLACE` on the same filesystem, verified again and fsynced with both directories; no destination is replaced and nothing is deleted. The result records source/destination, size, SHA256, identity metadata and preservation status for every prior proof.

Before preservation completes, checkpoints are written only inside the fresh nonce workspace. Thus a failed preflight or partial preservation does not overwrite a previous top-level result. Pending/preserved status remains in the nonce checkpoint for review. Only after preservation completes may the new top-level result be published and import begin. Source-catalog, plan, audit, refresh and every other existing output name remain in place. Old reports are evidence, not authority to bypass current preflight.

The runner never reads local configuration `.deb` contents itself. The importer owns archive verification, including any narrowly reviewed legitimate two-link local package pair. No generic alias allowance or archive mutation is introduced here.

## Ordering and integrity

1. The importer runs first, with original plan provenance still intact. It requires the authenticated full transaction, including every selected remote archive, every retained matching archive and local configuration archives; hashes all selected bytes; refuses mismatches or overwrites; and preserves unrelated cache entries and target state. Import success and every archive's verified status are checked in its nonce/plan/hash-bound report. Missing-only plans are insufficient.
2. The explicit `--package-stage` recovery then checks its native payload finding, reviewed classification, exact CF0/1df state and source/config/process/mount guards. It quarantines only proven stale lock/runtime files. Its return code, nonce, package-stage flag, performed flag and resulting exact sixteen stages are checked. No empty state is fabricated.
3. The configuration transport is checked again, and only `/usr/bin/lb chroot` is run. There is no fallback, force option, archive cleanup or manual alteration of completion flags on failure. Normal public live-build behavior, including its own cleanup and target package scripts, still applies.

APT 3.0.3 trusts cached archive size on a cache hit. Therefore `native_apt_cached_sha256_verified` is always false, with an explicit reason in the result. Integrity comes from hashing **all** full authenticated transaction archives in the importer, not a claim of native APT cached SHA verification. Public apt-get still performs its ordinary resolution/install processing; the runner does not weaken APT trust.

## Exact option propagation

Plain environment `APT_OPTIONS` fails because saved `config/common` assigns it again. Exact source has `Init_config_data` call `Read_conffiles` before `Prepare_config`; the latter preserves a nonempty APT_OPTIONS and init appends only an APT color option. `Get_conffiles` supports exported LB_CONFIG as a complete replacement list. The runner supplies the full normal list followed by one private final file:

```text
config/all config/common config/bootstrap config/chroot config/binary config/source
config/all.amd64 config/all.trixie
config/common.amd64 config/common.trixie
config/bootstrap.amd64 config/bootstrap.trixie
config/chroot.amd64 config/chroot.trixie
config/binary.amd64 config/binary.trixie
config/source.amd64 config/source.trixie
/project-output/package-stage-<nonce>/offline-options
```

The actual environment value is one space-separated string in precisely this order. Missing standard inputs stay absent. The final file contains exactly these bytes (including the final newline):

```sh
APT_OPTIONS="--yes -o Acquire::Retries=5 --no-download"
```

It is created exclusively mode0600 outside the target, pinned in the result and checked immediately before and after public lb. All private options, runner logs and intermediate runner output remain under `/project-output/package-stage-<nonce>/`. The separate existing importer retains its own staging and proof locations as documented by that helper.

The read-only transport probe runs a fixed native `/bin/sh -c` program, sources only the pinned conffile function, defines inert debug/error helpers, and calls the exact `Read_conffiles $(Common_conffiles)`. It reads only already pinned assignment configs plus the private overlay, and checks exact options and the effective apt/architecture/distribution/cache/initramfs values. It never calls Init_config_data, Prepare_config, a target executable, mount, APT or a stage helper. The result records the observed probe output only if it actually runs successfully. Static source review is not represented as a runtime probe.

The pinned frontend passes LB_CONFIG through `/usr/bin/env`; absent config/environment files cannot replace it. Nested public lb invocations receive the same selector. Reviewed chroot archive-acquisition call paths in `functions/packages.sh`, `functions/wrapper.sh`, `chroot_install-packages` and `chroot_archives` expand APT_OPTIONS into apt-get arguments before Chroot clears the target environment. The apt backend is required; aptitude is rejected by the transport probe. An archive acquisition omitted from the authenticated plan fails with `--no-download` rather than fetching it. Metadata updates, hooks, maintainer scripts and arbitrary network use are not a network sandbox; no claim of universal network isolation is made. Installer/source-only acquisition code is outside the invoked stage.

## Child output and monitoring

Importer, recovery and public lb output is merged as binary stdout/stderr and copied in blocks of at most 64 KiB to both its exclusive nonce log (`import.log`, `recovery.log`, `lb-chroot.log`) and the runner's flushed `sys.stdout.buffer`. The inherited guest build log/UART stream therefore receives actual child progress and the controller can preserve its complete guest log. Logging uses append mode and handles partial writes. Each child log is bounded to 64 MiB; exceeding that cap is a failure, not silent truncation.

Each child starts a new session with controlled argv, fixed working directory/environment and no stdin. A log, pipe or console write/flush error stops the owned process group: SIGTERM, up to ten seconds for orderly exit, then SIGKILL for any remaining descendants, and a wait to reap the direct child. This also runs on interruption of the observation loop, so a failed output sink cannot intentionally leave APT running unobserved. The normal child return code is preserved when all output succeeds, and the completed log is fsynced. Package installation has no arbitrary stage timeout; the ten-second bound applies only to failure cleanup. This behavior has source/AST review only; runtime observation and cleanup behavior remain unmeasured.

## Results and limits

`/project-output/package-stage-result.json` is bounded to 1 MiB and atomically replaced from the nonce workspace, with fsync. The nonce checkpoint is retained as `result.json`. It records helper/source/plan pins, configuration list/options, actual probe output, importer and recovery report hashes and return codes, public chroot return code, completion flags and the installed package manifest digest. Failure records `chroot_completed=false`, the error and retained partial stage logs in the nonce result (and the top-level result only after prior-proof preservation completes); it does not remove archives, flags or target state.

`chroot_completed=true` requires public lb return0, no target mounts or active package/build processes, absent lock/runtime flags, required source-defined public completion flags including both install/live package passes and chroot_hacks, and all target status records exactly `install ok installed`. All seventeen core package names match `scripts/audit-iso.py` and must be present unambiguously. Final target status is parsed as data by the native guest controller; no target program is executed to export the final manifest. Normal public lb itself runs target programs as designed.

The manifest `/project-output/package-stage.packages` contains sorted `package:architecture<TAB>version` lines; a nonce copy is retained. The root controller is explicitly allowed to upload this file along with the result and referenced import/recovery proofs and logs. `iso_verified` remains false even on success. Package stage completion does not establish ISO content, boot, installation, desktop, application or hardware behavior. Those independent gates still require real outputs and separate measurements.

Local review evidence under `.work/offline-stage-review/` preserves archive source pins, saved config pins, relevant exact source extracts and an acquisition-call inventory. No project module or helper has been executed on the host for this implementation.
