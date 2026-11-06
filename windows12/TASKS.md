# Stable tasks

Latest W12-040 BIOS evidence: actual offline Calamares completed all39jobs; ISO-free new-account/Wayland/root/sudo/basicXLSX observations passed. Review12720 stopped0 with unchangedbaseline; docs/CALAMARES_PREVIEW4.md. W12-005 remains open for clock-fixed NEW ISO, UEFI, broader workflow/reboot evidence. Missinghwclock future source fix implemented; new UEFI/fresh-builder code requires contained guest validation. No VM currently running; do not snapshot agent iso_media_review's partial implementation. Main before update1a72ec2f66677ac14f48bf51f37a965b616daabc.

## Current task checkpoint — overrides historical status rows below

Main before this update: `24f9ad931c190e0b3309beabbcd76a0943c307af`, clean; project `/home/avision/gitclone/AI-use/windows12/`; approximately73GiB free at parent observation.

| Task | Current evidence and next acceptance |
|---|---|
| W12-005 | Real unchanged preview4 ISO, content audit, BIOS D-I installation/ISO-free root proof and reviewed basic installed GUI observations exist. Normal Calamares, remaining workflows and firmware/hardware acceptance remain open. |
| W12-011 | Actual corrected D-I installation and ISO-free installed-root proof passed in `artifacts/install-passstdout-001/`; this is separate from Calamares and GUI acceptance. |
| W12-022 | Installed graphical session51793 completed0/guest-exited with read-only baseline unchanged and no cleanup errors. `docs/INSTALLED_DESKTOP_PREVIEW4.md` records default Wayland login/layout/menu, Dolphin/Kate, basic DOCX save/reopen/public export and lock/logout/relogin observations; automatic flags remain false. Full Office corpus and broader application/hardware coverage remain pending. |
| W12-040 next | Sole active VM75984: `artifacts/calamares-live-001/`, pristine ISO/new24GiB disk, KVM host CPU/2D virtio/BIOS/network none/7200s. Actual offline Calamares copy is running after reviewed vda-only summary and new public account. Poll/capture completion, preserve logs, then clean shutdown and subsequent ISO-free manual-disk child review. Do not start a duplicate guest. |
| W12-006 | Source checkpoint on main above; parent must review these project-only memory changes before the next nonforced synchronization. Generated disks/ISO/logs remain ignored and need independent preservation. |

Installed baseline SHA256 remains `58bcaea9b07c88797ac80fd8aed126862a1459561d061763a94764fecf74ffad`; ISO SHA256 remains `7d36b5847fba7240ee2795bb42ff3ea841652569b7eb983cfec6ea96968ae11c`. Normal UEFI/Secure Boot and physical hardware remain pending. No physical installation was performed.

| ID | Task | Depends | Owner | Status | Acceptance |
|---|---|---|---|---|---|
| W12-001 | Boundaries and persistent memory | none | lead | done | Sole repo located; six memory files in project |
| W12-002 | Architecture and compatibility research | 001 | research agent | done | Primary sources; supported/partial/alternative/unsupported; no untested claims |
| W12-003 | Contained build feasibility and implementation | 001 | build agent | implemented; restored25 guest tests and package gates pass | Runnable tooling; image writes isolated; verified inputs; fail closed |
| W12-004 | Desktop overlay and Office web integration | 002 | lead | preview4:36 guest tests/deterministic package pass; GUI pending | Runnable launchers, welcome/help, Windows-style desktop defaults |
| W12-005 | Integrate, build and validate milestone image | 003,004 | lead | real3.4GiB ISO built/hash/content audit passed; BIOS menu seen; diagnostic harness55tests pass; default Wayland black, modified X11 partialGUI; D-I8231 reached GRUB then late test pipeline failed; pass-stdout rerun93139 completed0; real ISO-free installed-root/configuration proof passed; sealed baseline retained; expanded82-test suite/package/shutdown passed; ISO-free GUI51793 active | Build logs/checksums; boot and install results or precise blockers |
| W12-006 | Release checkpoint and sync | 005 | lead | source checkpoints synchronized; release pending | Memory current; reviewed project-only commit synchronized |
| W12-007 | BIOS ISO evidence capture harness | 003,005 | research agent | guard integrated; all25 guest tests pass; ISO capture pending | Real contained ISO, screenshots/logs, new disposable disk only; no false success claim |
| W12-008 | Freeze release inputs and harden provenance | 005 | release_inputs/lead | cloud signature research complete (upstream missing); snapshots pending | Snapshot repositories/input authentication; reproducibility records and repeat build |
| W12-009 | Windows application compatibility milestone | 005 | release_inputs/lead | research complete; optional Bottles prototype preferred after base validation; unimplemented | Choose maintained runtime; exact app/version functional tests and honest limits |
| W12-010 | Reliable interrupted-builder resume | 003 | recovery agent/lead | frozen reboot, stale-lock/cache recovery and public chroot progress passed; full stages pending | Demonstrate interrupted long stage resumes with frozen source and refreshed proxy; current --resume is experimental |
| W12-011 | Automated BIOS disposable-disk installation and reboot harness | 005,012 | research agent/lead | real D-I and ISO-free disk boot passed; both QEMU runs0; GUI separate | Real D-I install callback plus installed boot evidence; no host devices; no Calamares certification |
| W12-012 | Verified project-local ISO inspection tools | 003 | build agent | done | Authenticated xorriso closure extracted to separate iso-tools; active QEMU files untouched |
| W12-013 | Bound live-disk synchronization temporary storage | 003 | build agent/lead | 18459 stopped0 afternetworkinterruption; no sync copies observed; pause branch untested | Exact-prefix age/inode audit, real disk preserved, measure bounded growth; no parallel exec polling |
| W12-014 | Restore execution access and reconcile original build | 001 | lead/infrastructure | done 2026-11-05: approved source restore verified; no old jobs/disks; no build active | Existing job/disk/output state established before any resume/new build; no duplicate VM |
| W12-015 | Read-only I/O telemetry for stale console diagnosis | 003 | boot_guard/lead | done: two actual QMP snapshots, counter delta validated | Serialized query-blockstats, existing guest unchanged, measured counters and honest limits |
| W12-016 | Conditional storage-backend feasibility | 013 | boot_guard/lead | research complete; prototype conditional, unimplemented | Primary sources, durability/test obligations; no current VM change; prototype only if sync blocks existing build |
| W12-017 | Recover current console without guest restart | 015 | boot_guard/build_restored/lead | done: UART ringbuf recovery and persistent reader executed | Observed serial0 stdio, preserve QMP pipe, bounded ringbuf output, no guest CPU/disk/boot change |
| W12-018 | Practical desktop release audit | 004,005 | desktop_audit/lead | source review complete; GUI execution pending | Concrete defects separated from unknowns, practical workflow validation before release |
| W12-019 | Real ISO content audit | 003,005 | boot_guard/lead | implemented/reviewed; authenticated tools startup passed; actual ISO pending | Frozen source/payload/core package/permissions/proxy/CA evidence; no boot claims |
| W12-020 | Interactive desktop validation harness | 003,005 | desktop_audit/lead | actual live attempt reached kernel/login; max/VGA default black; modified X11 panel/menu/Dolphin partial; constrained profiles55guesttests pass | Sole contained VM, safe QMP input/captures, new disk only, no false GUI pass |
| W12-021 | Controlled post-build image iteration plan | 005 | boot_guard/lead | source research complete; implementation/runtime pending | Preserve baseline/source; correct installer regeneration and manifests; version gates |
| W12-022 | ISO-free installed desktop QA | 011,020 | desktop_audit/lead | sealed proof producer/installed GUI child mode implemented/reviewed; 52 guest tests and actual QEMU graph pass; real installation/login pending | One-shot proof stamp, validated prior test disk, new writable child, baseline preserved; real reboot/GUI evidence |

| W12-023 | Fast contained unittest runner | 003 | lead/overlay_vm | done: third disposable VM35105 passed31tests/deterministic preview3 package/dpkg inspection; stopped | Fresh VM/source and bounded results; no host suite execution |
| W12-024 | Debian 13 host bootstrap | 014 | lead | done: prep72608 and TCG probe pass;91 authenticated packages | Native signed repositories/keyring; local extraction; actual startup and TCG probe; no host installs |

| W12-025 | Pinned Windows QA installer inputs | 009 | lead | done: real hashes/signature/offline/negative checks; no app execution | Locked public fixtures, no host execution, reproducible cache and honest assurance |

| W12-026 | Independent fixture-tool review | 025 | fixture_review_nov05/lead | done: reporting issue fixed; operational checks pass | Source review, bounded ownership, no false runtime claims |

| W12-027 | Sequential post-build validation queue | 005,019,007,011 | lead/fixture_review_nov05 | source reviewed; waiting-cancel passed;44581 canceled130 afternetworkstop; actual gates pending | No concurrent guests; frozen source/ISO/controller identity; cooperative helper cleanup; distinct evidence flags; actual gates pending |

| W12-028 | Stale live-build lock recovery | 010 | fixture_review_nov05/lead | done for observed lock: actual guard/quarantine/preservation passed; public chroot resumed; APT-cache030 recovered | Preserve original/cache/stage flags; guarded guest-only stale lock cleanup; actual resumed build evidence |

| W12-029 | Read-only stopped-builder inventory mode | 028 | lead/fixture_review_nov05/inspect_wrapper_review | done: inspections25448/41690/80287/72465 exit0/fresh complete reports; no ISO claims | Separate nonce-bound report, no recipe/cleanup, guarded existing disk, no false ISO success |

| W12-030 | Preserve/refresh corrupted target APT index cache | 028,029 | fixture_review_nov05/lead | done for observed snapshot: exact4cache quarantine/preservation and signed APT refresh advanced to9package upgrade; fullISO005active | Actual cache evidence; bounded quarantine; target dpkg/stages preserved; signed refresh and resumed build |

| W12-031 | Public Office workflow QA corpus | 005,009 | office_qa_fixtures_nov06/lead | done: realdeterministicgenerationtwice/ZIPCRC/XMLvalid; appworkflows pending | Deterministic runnable project-contained DOCX/XLSX/PPTX generator; public text/table/formulas/slides and expected values; actual open/edit/save/export/roundtrip in contained apps before compatibility claims |

| W12-032 | Bounded verified dependency prefetch and delivery | 005,030 | lead/package_plan_nov06/package_prefetch_nov06/guard_review_nov06 | historical catalog/1946-input plan passed; current inputs absent, no prefetch active; delivery/controller runtime pending | Actual signedcatalogSHA plan, bounded authorized batches, verified cache and nativeAPT verification after reviewed delivery; no signatures/TLS/permission bypass; actual resumed ISO build |

| W12-033 | Preview3 desktop and optional Windows Apps integration | 004,009 | lead/desktop_polish/windows_apps | implemented:31 guest tests and deterministic package pass; real GUI/app execution pending | Panel order, accessible offline help, installed Bottles routing with on-demand setup; no runtime preload |
| W12-034 | Exact post-chroot image finish contract | 032 | iso_finish/lead | documented; new installer inputs and executable bootstrap cache trust remain blockers | Preserve completed chroot, authenticate remaining inputs, public installer/binary/source then real ISO SHA/export |

| W12-035 | Restore execution and reconstruct lost preview3 build inputs | 014,023 | lead/infrastructure | upstream sparse ancestry restored; authenticated tools/cloud ready; real guest TLS/signature+36tests passed; full disk/ISO absent; total 7.84 GiB, expansion pending | Existing checkout/project boundary preserved; execution restored, original jobs/storage reconciled, current source restored, permitted dependencies and deliberate rebuild; no stale resume commands |

| W12-036 | Reject impossible resume before dependency access | 035 | lead/rebuild_review | source fixed; syntax and negative CLI checks passed; guest runtime pending | Retained disk/source/hash checked before tool/download/provenance; source validation before fresh disk; reject resume+prepare/probe |

| W12-037 | Managed sidecar proxy transport and bounded guest network proof | 035 | lead/proxy_helper/release_review | implemented/reviewed; real guest HTTPS/signature,36tests/package and shutdown passed | Fixed inherited upstream only; localhost relay; normal TLS and archive signatures; bounded connections; no direct fallback; provenance and actual contained evidence |

| W12-038 | Explicit contained VGA firmware for graphical gates | 012,020,022 | lead | actual missing-ROM failure reproduced; all 3 controllers fixed; real QEMU graph/readonly-baseline smoke and 52 guest tests pass | Only authenticated local VGA ROM; firmware startup and baseline preservation; OS/GUI validation still separate |

| W12-039 | Contained normal UEFI validation | 012,020 | lead | authenticated separate OVMF tools prepared; firmware descriptor/readme reviewed; actual UEFI boot/install pending | Read-only code, new writable vars copy, no physical devices; measured UEFI boot/install; Secure Boot separate |
| W12-040 | Actual graphical installer acceptance | 003,004,020 | lead | actual Calamares payload/config reviewed; offline live-user launch/partition/install/reboot pending | New disposable disk, normal account/admin/session, payload survives cleanup, ISO-free reboot and workflow evidence |

| ID | Task | Depends | Owner | Status | Acceptance |
|---|---|---|---|---|---|
| W12-041 | Explicit available-KVM test profiles | 003,011,020 | lead | reviewed/AST parsed; existing device access confirmed; guest/runtime validation pending | No host setup/fallback, fixed CPU choices, contained devices, actual KVM startup/desktop evidence |
| W12-042 | Honest manual installed-disk continuation | 020,040 | lead | BIOS-only wrapper and guest tests implemented/reviewed; runtime pending | Clean live provenance, stopped sealed baseline, readonly backing/new child, no ISO, distinct falseflags then reviewed boot/login/root evidence |

Current source-check47507 includes fresh-builder namespace/KVM/observer/QMP-lock safeguards plus10new guest tests; combined target97. OldISO normalUEFI live boot observed and stopped0/originalfirmwareunchanged; docs/UEFI_PREVIEW4.md. Corrected fresh build still not launched.

Combined source validation PASSED97guesttests/package/shutdown in artifacts/overlay-check-196e24e1e16eef4083a3ff138c4ab309, sourceSHA7e609eb2cef6c8fde337c4566a4d93a63fedac5011a33158fba07e6182e8f61a.64GiBfree/noVMactive. Ready to checkpoint and launch isolated clockfix-001 fullbuild.

W12-043 storage retention:11obsolete failed/check disks+derivedsquash removed,10.34GiB reclaimed; usefulauthenticatedinputs/caches and current/successfulbaselines retained. Retire old completedbuilder/oldbaselines after correctedcandidate acceptance. Currentclockfixbuild1524/monitor7783/queue64013 active; no duplicateVM. See latestHANDOFF.
