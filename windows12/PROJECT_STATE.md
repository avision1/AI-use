# Project state — 2026-11-06 UTC

## Current execution checkpoint — 2026-11-05 America/Chicago
Execution works in the supplied fresh workspace. Sole checkout: `/workspace/scratch/a8ea18c8241a/AI-use`; project boundary: its `windows12/` directory. Source restored from main `8619b2c`; no sibling project changed. Process inventory found no QEMU/build/monitor/validation workers. Before wrapper refusal checks, `.work/` and `artifacts/` were absent: old disk, source archive, cloud image, tools, cache and package plan are unavailable. Historical handles/counts below are not current inputs.

Current environment network allowlist excludes Debian package/security/cloud hosts. No denied download was retried or alternate route used. No guest build, runtime suite or ISO gate ran. Previous 31-test/package results remain historical. No ISO exists.

Independent read-only review confirmed two controller defects now fixed: retained disk/source/hash checks precede dependency checks/downloads; fresh source validation precedes disk creation. Resume+prepare/probe options are rejected. Validation: Python syntax parsing, actual negative CLI refusal checks and diff checks; guest/runtime verification pending.

User is considering Linux Mint laptop as build environment. Local Codex can continue from these checkpoints. build-tools.py explicitly supports Debian13/Ubuntu24.04; inspect/adapt Mint support rather than assuming compatibility. Keep target construction inside the project VM, never on the laptop host.

Next: in an environment with permitted Debian/cloud access, reconcile source/jobs/storage. With no artifacts, set project-local HOME/TMP/XDG from RUNBOOK, prepare tools for the actual host, then run build-vm.py --probe, --prepare and a deliberate fresh build (no --resume). Monitor storage safeguards. Require real ISO content/boot/install/GUI and Windows-app gates. Never use historical plan/nonce commands unless exact inputs are recovered and validated.


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

## Current blocker
Network policy blocked https://deb.debian.org:443. No bypass attempted. Offline cache check:680 valid cached /1946 planned,1266 missing,2.049GB full transaction. No prefetch worker active. More installer/binary inputs are required beyond that transaction, documented in docs/FINISH_IMAGE_STAGE.md. These missing inputs prevent honest ISO completion in this environment.

## Historical baseline — not currently present
Retained standalone24GiB virtual builder previously passed offline QCOW2 check. Frozen preview2 checks.tar SHA256f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff unchanged. Current source preview3 is separate and must use a deliberate new candidate; do not silently modify frozen baseline. Runtime artifacts are ignored and can be pruned; Git preserves source and instructions only.

## Compatibility and lean experience
Windows-like desktop conventions are implemented but untested graphically. Linux/KDE preferences and native apps remain available. Optional Bottles/Wine and Proton are the compatibility direction; no Windows runtime/app has yet executed. Office web functionality partial; LibreOffice offline alternative; current native Microsoft365 desktop unsupported. Smaller kde-plasma-desktop selection avoids the full application collection, but real installed size/RAM/startup/background services remain measurement gates.

## Next action
Follow HANDOFF current checkpoint; historical plan/nonce files are missing. Restore permitted package access, complete authenticated inputs, execute guarded chroot, cover installer inputs, finish ISO and run boot/install/desktop gates. Do not launch a stage on incomplete cache or claim source/tests are a release. User authorizes helpful subagents and regular project-only commits/pushes to main without reasking.
