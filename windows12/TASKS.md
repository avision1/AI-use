# Stable tasks
| ID | Task | Depends | Owner | Status | Acceptance |
|---|---|---|---|---|---|
| W12-001 | Boundaries and persistent memory | none | lead | done | Sole repo located; six memory files in project |
| W12-002 | Architecture and compatibility research | 001 | research agent | done | Primary sources; supported/partial/alternative/unsupported; no untested claims |
| W12-003 | Contained build feasibility and implementation | 001 | build agent | implemented; restored25 guest tests and package gates pass | Runnable tooling; image writes isolated; verified inputs; fail closed |
| W12-004 | Desktop overlay and Office web integration | 002 | lead | preview2 guest unit/package checks pass; GUI pending | Runnable launchers, welcome/help, Windows-style desktop defaults |
| W12-005 | Integrate, build and validate milestone image | 003,004 | lead/build agent | resume11322 clean failure1: stale bootstrap_cache lock; guest25 tests/package rerun pass; repair research | Build logs/checksums; boot and install results or precise blockers |
| W12-006 | Release checkpoint and sync | 005 | lead | source checkpoints synchronized; release pending | Memory current; reviewed project-only commit synchronized |
| W12-007 | BIOS ISO evidence capture harness | 003,005 | research agent | guard integrated; all25 guest tests pass; ISO capture pending | Real contained ISO, screenshots/logs, new disposable disk only; no false success claim |
| W12-008 | Freeze release inputs and harden provenance | 005 | release_inputs/lead | cloud signature research complete (upstream missing); snapshots pending | Snapshot repositories/input authentication; reproducibility records and repeat build |
| W12-009 | Windows application compatibility milestone | 005 | release_inputs/lead | research complete; optional Bottles prototype preferred after base validation; unimplemented | Choose maintained runtime; exact app/version functional tests and honest limits |
| W12-010 | Reliable interrupted-builder resume | 003 | recovery agent/lead | frozen reboot, stale-lock/cache recovery and public chroot progress passed; full stages pending | Demonstrate interrupted long stage resumes with frozen source and refreshed proxy; current --resume is experimental |
| W12-011 | Automated BIOS disposable-disk installation and reboot harness | 005,012 | research agent/lead | implemented; unexecuted | Real D-I install callback plus installed boot evidence; no host devices; no Calamares certification |
| W12-012 | Verified project-local ISO inspection tools | 003 | build agent | done | Authenticated xorriso closure extracted to separate iso-tools; active QEMU files untouched |
| W12-013 | Bound live-disk synchronization temporary storage | 003 | build agent/lead | 18459 stopped0 afternetworkinterruption; no sync copies observed; pause branch untested | Exact-prefix age/inode audit, real disk preserved, measure bounded growth; no parallel exec polling |
| W12-014 | Restore execution access and reconcile original build | 001 | lead/infrastructure | done 2026-11-05: source restored; no old jobs/disks; new build active | Existing job/disk/output state established before any resume/new build; no duplicate VM |
| W12-015 | Read-only I/O telemetry for stale console diagnosis | 003 | boot_guard/lead | done: two actual QMP snapshots, counter delta validated | Serialized query-blockstats, existing guest unchanged, measured counters and honest limits |
| W12-016 | Conditional storage-backend feasibility | 013 | boot_guard/lead | research complete; prototype conditional, unimplemented | Primary sources, durability/test obligations; no current VM change; prototype only if sync blocks existing build |
| W12-017 | Recover current console without guest restart | 015 | boot_guard/build_restored/lead | done: UART ringbuf recovery and persistent reader executed | Observed serial0 stdio, preserve QMP pipe, bounded ringbuf output, no guest CPU/disk/boot change |
| W12-018 | Practical desktop release audit | 004,005 | desktop_audit/lead | source review complete; GUI execution pending | Concrete defects separated from unknowns, practical workflow validation before release |
| W12-019 | Real ISO content audit | 003,005 | boot_guard/lead | implemented/reviewed; authenticated tools startup passed; actual ISO pending | Frozen source/payload/core package/permissions/proxy/CA evidence; no boot claims |
| W12-020 | Interactive desktop validation harness | 003,005 | desktop_audit/lead | implemented/reviewed; real ISO execution pending | Sole contained VM, safe QMP input/captures, new disk only, no false GUI pass |
| W12-021 | Controlled post-build image iteration plan | 005 | boot_guard/lead | source research complete; implementation/runtime pending | Preserve baseline/source; correct installer regeneration and manifests; version gates |
| W12-022 | ISO-free installed desktop QA | 011,020 | desktop_audit/lead | one-shot proof source reimplemented/syntax checked; validated-disk GUI/helper/tests pending | One-shot proof stamp, validated prior test disk, new writable child, baseline preserved; real reboot/GUI evidence |

| W12-023 | Fast contained unittest runner | 003 | lead | prior uncommitted work lost; pending | Fresh VM/source and bounded results; no host suite execution |
| W12-024 | Debian 13 host bootstrap | 014 | lead | done: prep72608 and TCG probe pass;91 authenticated packages | Native signed repositories/keyring; local extraction; actual startup and TCG probe; no host installs |

| W12-025 | Pinned Windows QA installer inputs | 009 | lead | done: real hashes/signature/offline/negative checks; no app execution | Locked public fixtures, no host execution, reproducible cache and honest assurance |

| W12-026 | Independent fixture-tool review | 025 | fixture_review_nov05/lead | done: reporting issue fixed; operational checks pass | Source review, bounded ownership, no false runtime claims |

| W12-027 | Sequential post-build validation queue | 005,019,007,011 | lead/fixture_review_nov05 | source reviewed; waiting-cancel passed;44581 canceled130 afternetworkstop; actual gates pending | No concurrent guests; frozen source/ISO/controller identity; cooperative helper cleanup; distinct evidence flags; actual gates pending |

| W12-028 | Stale live-build lock recovery | 010 | fixture_review_nov05/lead | done for observed lock: actual guard/quarantine/preservation passed; public chroot resumed; APT-cache030 recovered | Preserve original/cache/stage flags; guarded guest-only stale lock cleanup; actual resumed build evidence |

| W12-029 | Read-only stopped-builder inventory mode | 028 | lead/fixture_review_nov05/inspect_wrapper_review | done: inspections25448/41690/80287/72465 exit0/fresh complete reports; no ISO claims | Separate nonce-bound report, no recipe/cleanup, guarded existing disk, no false ISO success |

| W12-030 | Preserve/refresh corrupted target APT index cache | 028,029 | fixture_review_nov05/lead | done for observed snapshot: exact4cache quarantine/preservation and signed APT refresh advanced to9package upgrade; fullISO005active | Actual cache evidence; bounded quarantine; target dpkg/stages preserved; signed refresh and resumed build |

| W12-031 | Public Office workflow QA corpus | 005,009 | office_qa_fixtures_nov06/lead | done: realdeterministicgenerationtwice/ZIPCRC/XMLvalid; appworkflows pending | Deterministic runnable project-contained DOCX/XLSX/PPTX generator; public text/table/formulas/slides and expected values; actual open/edit/save/export/roundtrip in contained apps before compatibility claims |

| W12-032 | Bounded verified dependency prefetch and delivery | 005,030 | lead/package_plan_nov06/package_prefetch_nov06/guard_review_nov06 | first2exports safelyfailedexpectedhooks/missinggpgv; SQVfixed; deliveryhelper/newexplicitguard source reviewed; runtime/controllerintegration pending | Actual signedcatalogSHA plan, bounded authorized batches, verified cache and nativeAPT verification after reviewed delivery; no signatures/TLS/permission bypass; actual resumed ISO build |
