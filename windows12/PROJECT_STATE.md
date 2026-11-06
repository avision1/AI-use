# Project state — 2026-11-06 UTC

## Milestone
W12-005 first installable Debian13/amd64 KDE preview remains incomplete. **No ISO, live GUI, successful installation or Windows application execution has been validated.** All runtime jobs are stopped. Work is limited to the existing AI-use/windows12 project.

## Source implemented and measured
- Preview3: Windows-style panel defaults, menu/task ordering repair, responsive accessible offline help, Office web launchers, optional Windows Applications/Bottles routing. No preloaded Wine stack/background service added.
- Actual disposable VM run35105:31 tests passed; desktop package built twice byte-identically, inspected with dpkg-deb. Preview3 package9950bytes SHA256864088a1111468d49a17d5e28d16534b7e013a975795cd3acfb0b09c3dd2beb9. Evidence artifacts/overlay-check-6c5d49ef8e31a0e6f59f2303c4b5f1c7; shutdown proved. Tests mock application launching; no GUI/app execution claim.
- Cached-input unit/package runner implemented and exercised; distinct new disk/source and shared VM lock preserve retained builder. Earlier two route-preflight failures retained and corrected.
- Full selected transaction signed-catalog exporter, bounded prefetch, complete archive importer, explicit package-stage guard and no-download public chroot controller implemented/reviewed. Catalog refresh and full plan passed; actual delivery/chroot completion pending.
- ISO content/BIOS/live GUI/D-I disposable installation/sequential validation tools implemented; actual ISO gates pending. Windows and Office QA fixtures validated as inputs only.

## Current blocker
Network policy blocked https://deb.debian.org:443. No bypass attempted. Offline cache check:680 valid cached /1946 planned,1266 missing,2.049GB full transaction. No prefetch worker active. More installer/binary inputs are required beyond that transaction, documented in docs/FINISH_IMAGE_STAGE.md. These missing inputs prevent honest ISO completion in this environment.

## Preserved baseline
Retained standalone24GiB virtual builder previously passed offline QCOW2 check. Frozen preview2 checks.tar SHA256f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff unchanged. Current source preview3 is separate and must use a deliberate new candidate; do not silently modify frozen baseline. Runtime artifacts are ignored and can be pruned; Git preserves source and instructions only.

## Compatibility and lean experience
Windows-like desktop conventions are implemented but untested graphically. Linux/KDE preferences and native apps remain available. Optional Bottles/Wine and Proton are the compatibility direction; no Windows runtime/app has yet executed. Office web functionality partial; LibreOffice offline alternative; current native Microsoft365 desktop unsupported. Smaller kde-plasma-desktop selection avoids the full application collection, but real installed size/RAM/startup/background services remain measurement gates.

## Next action
Follow current HANDOFF exact plan/nonce/commands. Restore permitted package access, complete authenticated inputs, execute guarded chroot, cover installer inputs, finish ISO and run boot/install/desktop gates. Do not launch a stage on incomplete cache or claim source/tests are a release. User authorizes helpful subagents and regular project-only commits/pushes to main without reasking.
