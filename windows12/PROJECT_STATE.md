# Project state — 2026-11-06 UTC

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

## Current installed-desktop validation checkpoint
The final combined candidate passed all 52 tests in the disposable VM, including 16 installed-desktop proof/child/cleanup tests. Evidence: `artifacts/overlay-check-b7f9782b360e7911f2de5bafdf5ecd2a/`; source SHA256 `f05f9ded24ef5216ecbceed14e71b94b17e3c8a22d2a7c4f5d52d67e4dea349c`. Real guest proxy TLS and Debian signature verification passed again, preview4 package stayed byte-identical, and shutdown was confirmed. No current test worker remains active.

The installer now seals the stopped proven baseline by SHA256 and file identity. `desktop-test.py --installed-result <successful-result.json>` validates that seal, original ISO/phase provenance and serial proof, creates a fresh child with an explicitly read-only baseline, boots without ISO/direct kernel, and checks baseline preservation after cleanup. It retains false GUI/login/workflow flags until actual manual evidence. No real installed baseline exists yet.

An actual QEMU graph probe first found missing default VGA ROM lookup in locally extracted tools. All three graphical controllers now name the authenticated project-local SeaBIOS VGA ROM explicitly. The corrected real QEMU smoke accepted the read-only baseline/writable child graph, ran firmware, stopped, and left the baseline hash/stat unchanged: `artifacts/installed-graph-probe-3262f4ceb78252c8/`. This was a tiny synthetic disk firmware probe, not OS boot or GUI validation.

Public Office QA originals are regenerated under `artifacts/office-fixtures/`; all four pinned Windows QA installers are cached and verified, including the required Notepad++ publisher signature, under `.work/compat/`. None has executed in an app. Verified source main before this checkpoint: `bbb0471d30c8f32a44b9478ecc8199f254d450ec`. Native Git ancestry is now available without sibling materialization. The earlier waiting-only supervisor was cancelled before this reviewed source iteration; no full builder disk/ISO was created. Storage remains 7.84 GiB total; expansion is still required before the full build.


## Historical execution interruption
A resume attempt found the supplied checkout at old project commit 696bc1c, with no windows12/.work/builder or windows12/artifacts directories. The committed preview3 source on GitHub is intact (remote main759c468e750c405f93d60e0e858429384d3cd97e at inspection); later sibling changes were preserved.

Before any VM launch, current-source restoration was attempted through the GitHub connector in the existing checkout. All60 required writes failed because the execution service returned: Failed to create unified exec process: exec-server transport disconnected. Successful restoration writes:0. No build, tests, downloads or VM launch occurred in this attempt. Runtime/file operations stopped after the service failure. Any process/disk state after disconnection is UNKNOWN until execution access is restored; historical handles are not live evidence.

The old builder disk, frozen archive,680 downloaded archives, full plan and validation artifacts are absent from the observed workspace. Their hashes/results below are historical evidence, not currently available files. Git preserves source/instructions, not ignored runtime outputs. Previous network-policy denial for deb.debian.org remains unresolved; no retry, alternate origin/proxy, tool route or approval bypass was attempted.

Recovery requires functioning execution access and permitted Debian dependency access. Restore only windows12/ from freshly verified remote main into the existing checkout; preserve unrelated directories and Git history. Reconcile original jobs/storage first. If prior artifacts cannot be recovered, deliberately rebuild preview3 from source using the pinned input recipe; do not run the old --resume or old plan/nonce commands against missing files. Then require real package/ISO/boot/install/GUI gates. The prior31-test pass remains historical; no new test result or ISO is claimed. No redundant agents were launched because they could not resolve the unavailable build environment.

## Historical milestone
W12-005 first installable Debian13/amd64 KDE preview remains incomplete. **No ISO, live GUI, successful installation or Windows application execution has been validated.** Previous checkpoint jobs stopped; current post-disconnection state is UNKNOWN. Work is limited to the existing AI-use/windows12 project.

## Source implemented and measured
- Preview3: Windows-style panel defaults, menu/task ordering repair, responsive accessible offline help, Office web launchers, optional Windows Applications/Bottles routing. No preloaded Wine stack/background service added.
- Actual disposable VM run35105:31 tests passed; desktop package built twice byte-identically, inspected with dpkg-deb. Preview3 package9950bytes SHA256864088a1111468d49a17d5e28d16534b7e013a975795cd3acfb0b09c3dd2beb9. Evidence artifacts/overlay-check-6c5d49ef8e31a0e6f59f2303c4b5f1c7; shutdown proved. Tests mock application launching; no GUI/app execution claim.
- Cached-input unit/package runner implemented and exercised; distinct new disk/source and shared VM lock preserve retained builder. Earlier two route-preflight failures retained and corrected.
- Full selected transaction signed-catalog exporter, bounded prefetch, complete archive importer, explicit package-stage guard and no-download public chroot controller implemented/reviewed. Catalog refresh and full plan passed; actual delivery/chroot completion pending.
- ISO content/BIOS/live GUI/D-I disposable installation/sequential validation tools implemented; actual ISO gates pending. Windows and Office QA fixtures validated as inputs only.

## Historical dependency blocker
The earlier network policy blocked https://deb.debian.org:443. No bypass attempted. Offline cache check:680 valid cached /1946 planned,1266 missing,2.049GB full transaction. No prefetch worker active. More installer/binary inputs are required beyond that transaction, documented in docs/FINISH_IMAGE_STAGE.md. These missing inputs prevent honest ISO completion in this environment.

## Historical baseline — not currently present
Retained standalone24GiB virtual builder previously passed offline QCOW2 check. Frozen preview2 checks.tar SHA256f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff unchanged. Current source preview3 is separate and must use a deliberate new candidate; do not silently modify frozen baseline. Runtime artifacts are ignored and can be pruned; Git preserves source and instructions only.

## Compatibility and lean experience
Windows-like desktop conventions are implemented but untested graphically. Linux/KDE preferences and native apps remain available. Optional Bottles/Wine and Proton are the compatibility direction; no Windows runtime/app has yet executed. Office web functionality partial; LibreOffice offline alternative; current native Microsoft365 desktop unsupported. Smaller kde-plasma-desktop selection avoids the full application collection, but real installed size/RAM/startup/background services remain measurement gates.

## Next action
Follow HANDOFF current checkpoint; historical plan/nonce files are missing. Restore permitted package access, complete authenticated inputs, execute guarded chroot, cover installer inputs, finish ISO and run boot/install/desktop gates. Do not launch a stage on incomplete cache or claim source/tests are a release. User authorizes helpful subagents and regular project-only commits/pushes to main without reasking.

## Owned waiting build supervisor
Owner `/root`, unified execution session `50558`, Python PID `4619`. `.work/work/fresh-supervisor.json` currently records `waiting-storage`, `build_started=false`; minimum available storage32GiB. It will recheck the frozen source inventory, refuse an existing builder disk, then invoke the guarded fresh build, start the existing storage monitor and run sequential content/BIOS/install gates only after successful ISO export. GUI/workflow certification remains separate. Do not launch a duplicate. Read the owned session/state/controller logs and reconcile PID/runner lock/QMP before any restart. While still waiting, `.work/work/cancel-fresh-supervisor` cancels only this supervisor before launch. Unknown handles are not proof of termination. The watcher and transient inputs are ignored and do not survive pruning; source/memory are preserved on main.
