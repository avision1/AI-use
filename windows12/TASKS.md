# Stable tasks
| ID | Task | Depends | Owner | Status | Acceptance |
|---|---|---|---|---|---|
| W12-001 | Boundaries and persistent memory | none | lead | done | Sole repo located; six memory files in project |
| W12-002 | Architecture and compatibility research | 001 | research agent | done | Primary sources; supported/partial/alternative/unsupported; no untested claims |
| W12-003 | Contained build feasibility and implementation | 001 | build agent | implemented; historical guest gates passed; tools restoring | Runnable tooling; image writes isolated; verified inputs; fail closed |
| W12-004 | Desktop overlay and Office web integration | 002 | lead | unit checks passed; GUI pending | Runnable launchers, welcome/help, Windows-style desktop defaults |
| W12-005 | Integrate, build and validate milestone image | 003,004 | lead/build agent | rebuild active after confirmed workspace loss | Build logs/checksums; boot and install results or precise blockers |
| W12-006 | Release checkpoint and sync | 005 | lead | pending | Memory current; reviewed project-only commit synchronized |
| W12-007 | BIOS ISO evidence capture harness | 003,005 | research agent | guard integrated; guest24/25 passed; fixture corrected, retest pending | Real contained ISO, screenshots/logs, new disposable disk only; no false success claim |
| W12-008 | Freeze release inputs and harden provenance | 005 | unassigned | pending | Snapshot repositories/input authentication; reproducibility records and repeat build |
| W12-009 | Windows application compatibility milestone | 005 | unassigned | pending | Choose maintained runtime; exact app/version functional tests and honest limits |
| W12-010 | Reliable interrupted-builder resume | 003 | recovery agent/lead | metadata reboot passed; staged replay pending | Demonstrate interrupted long stage resumes with frozen source and refreshed proxy; current --resume is experimental |
| W12-011 | Automated BIOS disposable-disk installation and reboot harness | 005,012 | research agent/lead | implemented; unexecuted | Real D-I install callback plus installed boot evidence; no host devices; no Calamares certification |
| W12-012 | Verified project-local ISO inspection tools | 003 | build agent | done | Authenticated xorriso closure extracted to separate iso-tools; active QEMU files untouched |
| W12-013 | Bound live-disk synchronization temporary storage | 003 | build agent/lead | cleanup historically verified; re-establish monitor | Exact-prefix age/inode audit, real disk preserved, measure bounded growth; no parallel exec polling |

| W12-014 | Restore execution access and reconcile original build | 001 | lead/infrastructure | done: shell restored; old workspace absent | Existing job/disk/output state established before any resume/new build; no duplicate VM |
