# Windows12 restart handoff — 2026-11-06 UTC

## Current execution checkpoint — 2026-11-05 America/Chicago (preview4 build preparation)
Sole project: `/workspace/AI-use/windows12/`. Network-enabled execution reaches the inherited proxy normally; previous curl7 failures were from restricted execution mode, not proof of a broken proxy service. Preserve inherited proxy/TLS configuration. Native filtered Git fetch now works; local main was reconciled to upstream `9107ef1` with only windows12 materialized and all 279 outside-project index paths excluded. The earlier source-equivalent snapshot remains only historical recovery evidence. User explicitly authorizes default publishing to main when every changed path is under windows12, and useful subagents.

Authenticated VM and ISO tools are extracted locally; QEMU TCG firmware probe passed. Pinned dated cloud image and original checksum manifest are present and verified. No full builder disk or ISO exists. Both disposable checks below stopped successfully; no build/validation worker remains active.

Preview4 fixes the build controller for the actual sidecar hostname: a bounded localhost-only TCP relay forwards bytes solely to the inherited HTTP proxy. Existing localhost mapping remains; credentials/unsupported URL forms fail closed. Guest TLS uses the configured public build CA; no alternate egress or TLS/signature waiver. Run provenance includes the helper hash and transport. Welcome guidance now reflects the optional Windows Applications entry, without claiming validated app compatibility.

Current runtime evidence:
- `artifacts/overlay-check-29ef3917036e8e6e483675c9ed5ba943/`: all 36 guest tests passed, deterministic double packaging and dpkg inspection passed, guest shutdown confirmed.
- `artifacts/overlay-check-56926e9e1c18e27f16c827b57d458590/`: actual guest HTTPS fetch of fixed Debian trixie InRelease through relay, TLS and archive signature verified; all 36 tests/package gates passed again; shutdown confirmed. Source SHA256 `51d7dd2e7958f697cb07fcc8385b593d027355ca254492ea78a56f2d3ffb878b`; later host-only provenance capture/storage refusal refinements passed syntax/actual negative CLI checks.
- Preview4 package: 9,970 bytes, SHA256 `cf4652f5ef2054388a6377e908c2673c78a7c003cee9362e003a9c61f4aa8075`. No ISO/boot/install/GUI/Windows-app support is inferred.

Current blocker: filesystem total 7.84 GiB, free approximately6.82GiB. User is arranging expansion to 40+ GiB. Full build/export and existing installation gate cannot fit. Fresh build now refuses below 8 GiB free before dependency access or disk creation; that threshold is not a complete build budget. Do not lower test/storage gates or start a doomed build. No host package installation, mounts, physical disk changes, sibling writes or proxy bypass.

Next: observe expanded capacity, reconcile workers/runner lock/QMP again, then from this project with RUNBOOK's project-local writable environment and network-enabled execution run `python3 -B scripts/build-vm.py` (fresh, no --resume). Cached tools/cloud input are ready. Start the existing storage monitor with auto-cleanup. After actual ISO/export require content audit, BIOS/live GUI, disposable installation, ISO-free installed boot and application workflows. See `docs/PROXY_TRANSPORT.md`. Mint remains an optional environment; bootstrap explicitly supports Debian13/Ubuntu24.04 and must be adapted/verified before claiming Mint support.

## Scope and authorization
Current sole checkout/project boundary is recorded above; repository is `avision1/AI-use`.
Every write, dependency, cache, temporary file, log and disk stays inside this folder. Only ordinary parent `.git` metadata is excepted. Preserve root and sibling projects, including concurrent commits. User explicitly authorized regular direct pushes to main and helpful subagents; no routine push approval needed. Never force-push. No host packages, mounts, partitions, boot changes or physical installation.

## Current truth
**Current tools/cloud input and preview4 guest checks are ready; full build awaits the user-arranged storage expansion. No ISO exists.** The checkpoint above supersedes historical runtime/network statements below.

## Historical execution interruption
A resume attempt found the supplied checkout at old project commit 696bc1c, with no windows12/.work/builder or windows12/artifacts directories. The committed preview3 source on GitHub is intact (remote main759c468e750c405f93d60e0e858429384d3cd97e at inspection); later sibling changes were preserved.

Before any VM launch, current-source restoration was attempted through the GitHub connector in the existing checkout. All60 required writes failed because the execution service returned: Failed to create unified exec process: exec-server transport disconnected. Successful restoration writes:0. No build, tests, downloads or VM launch occurred in this attempt. Runtime/file operations stopped after the service failure. Any process/disk state after disconnection is UNKNOWN until execution access is restored; historical handles are not live evidence.

The old builder disk, frozen archive,680 downloaded archives, full plan and validation artifacts are absent from the observed workspace. Their hashes/results below are historical evidence, not currently available files. Git preserves source/instructions, not ignored runtime outputs. Previous network-policy denial for deb.debian.org remains unresolved; no retry, alternate origin/proxy, tool route or approval bypass was attempted.

Recovery requires functioning execution access and permitted Debian dependency access. Restore only windows12/ from freshly verified remote main into the existing checkout; preserve unrelated directories and Git history. Reconcile original jobs/storage first. If prior artifacts cannot be recovered, deliberately rebuild preview3 from source using the pinned input recipe; do not run the old --resume or old plan/nonce commands against missing files. Then require real package/ISO/boot/install/GUI gates. The prior31-test pass remains historical; no new test result or ISO is claimed. No redundant agents were launched because they could not resolve the unavailable build environment.

## Completed previous session
- Reviewed/integrated full archive hash verification, import-before-recovery and public `lb chroot` continuation. Bare --resume now refuses bootstrap replay. Guest stage execution remains pending full inputs.
- Preview3 adds Windows Applications menu entry: launches installed user/system Bottles, otherwise displays local optional setup guidance. No runtime preload, automatic remote changes or installations.
- Fixed partial fresh-panel menu/task ordering; improved responsive/keyboard-accessible offline help. Actual Plasma/GUI verification pending.
- Added `scripts/check-overlay-vm.py`: cached pinned cloud input, new child disk, fresh source snapshot, shared VM exclusion, guest tests and deterministic packaging; never alters retained builder/source.
- ISO finish review established remaining public order and additional input gaps in `docs/FINISH_IMAGE_STAGE.md`. Installer/binary have downloads beyond the current desktop plan; do not invent an unsafe resume wrapper.

## Verified preview3 result
Runtime session35105 completed0, QEMU stopped. Evidence:
`artifacts/overlay-check-6c5d49ef8e31a0e6f59f2303c4b5f1c7/`.
- 31 guest unit tests passed; no host suite execution.
- Desktop package built twice identically and dpkg-deb inspected.
- `windows12-desktop_0.1.0~preview3_all.deb`: 9950 bytes, SHA256 `864088a1111468d49a17d5e28d16534b7e013a975795cd3acfb0b09c3dd2beb9`.
- Source snapshot SHA256 `0063122bc5662034c9126819c5fb5fb39dd12f4ff278442403943f1357b09bd7`.
- Exact all-table IPv4/IPv6 default-route queries removed measured forwarding IPv6 RA routes; before/after evidence retained. Default routes absent at check time is not a permanent network-sandbox claim.
- `passed=true`, `iso_verified=false`, host `qemu_stopped=true`.
Earlier runs bae0abb730a637f4e68ce5ea6f87d3d5 and85b0ee71da548eff8e8a1c7ca57052ad failed before tests on route handling; preserve evidence. Final exact-prefix/measured-route logic fixed those failures. No additional check needed absent changes.

## Historical build blocker and previously preserved inputs
Environment policy terminated prefetch session42550: access to `https://deb.debian.org:443` blocked. Do not work around permission/transport policy. Offline revalidation returned2 (incomplete): **680/1946 valid archives;1266 missing**. Offline stopped_on_auth=false does not establish network permission.
Full signed-catalog plan: `artifacts/package-plan-1793932073521244203/package-download-plan.json`, nonce `f405608a78a6be1a66da098684917d9b`, SHA256 `987ba05bd717a47df4a08d91a55f7089eb333461a337da2b3c91a39c462bfc6f`,1946 remote inputs/2049224880 bytes.
At the previous checkpoint the main builder `.work/builder/build.qcow2` was preserved; it is absent from the current observed workspace; frozen `.work/builder/checks.tar` SHA256 `f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff`. Current retained target is CF0/1df reviewed144-package state. See package-stage docs for exact provenance. Last catalog refresh passed native update and preserved protected state.
Preview3 source is **not** in that frozen preview2 builder. Do not replace its pinned package/source in-place. Preserve baseline and deliberately create a new candidate when ready. Git saves source/memory, not ignored VM disks, inputs or artifacts; pruning requires documented reconstruction.

## Historical next steps — only if exact retained inputs are recovered
1. Restore execution and reconcile current remote/head, source/status, VM locks/QMP and ignored artifact survival. Read AGENTS, PROJECT_STATE, TASKS, DECISIONS, RUNBOOK. Keep the same project boundary.
2. Dependency access must be permitted before further fetching. Once that is available, run bounded prefetch from this directory with project-local HOME/TMP/XDG:
   `python3 -B scripts/prefetch-packages.py artifacts/package-plan-1793932073521244203/package-download-plan.json --expected-nonce f405608a78a6be1a66da098684917d9b --limit 100 --workers 4`
   Respect denial; no alternate origin/proxy workaround. Stop on errors; repeat only authorized successful batches. Cache must be fully verified before launch.
3. With the entire cache present, run `python3 -B scripts/build-vm.py --resume --continue-package-stage artifacts/package-plan-1793932073521244203/package-download-plan.json`. Require actual importer/recovery/config-probe/public-chroot proofs. This produces no ISO by itself.
4. Establish trusted bootstrap-cache and additional installer/binary input coverage; implement reviewed exact finish continuation using `docs/FINISH_IMAGE_STAGE.md`. Never rerun bootstrap over completed target.
5. Require actual nonempty ISO, complete logs, host SHA and provenance; then content audit, BIOS boot, live GUI, disposable installer and ISO-free installed reboot. Validate Calamares separately from D-I harness. UEFI/hardware/app acceptance remain separate.
6. Build preview3 candidate deliberately; execute Wine/Bottles x64/x86 install/open/save/reopen/uninstall and desktop workflows, with measured size/startup/process use. No blanket app parity claims.

## Git checkpoints
Published recovery `1cdfed0610387cb63a271ddf3f1abdcafb0b55ec`; desktop source `8a670c026750b3892ee129fe744dd037a2a7fe0c`; checker checkpoint `2eaa9eb8b275d77c1583bf3a41e5a785e89912c3`. Final validation checkpoint follows this file; inspect actual remote. Native push lacks credentials, authenticated create_tree/create_commit/nonforced update_ref works. Base each tree on freshly verified remote main; preserve sibling advancement. Local source-equivalent commits may have different SHAs. Do not reset files or stage apparent outside-project deletions. Prior main-push approval block was resolved by explicit user permission.
