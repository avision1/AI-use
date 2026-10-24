# Stable tasks
| ID | Task | Depends | Owner | Status | Acceptance |
|---|---|---|---|---|---|
| W12-001 | Boundaries and persistent memory | none | lead | done | Sole repo located; six memory files in project |
| W12-002 | Architecture and compatibility research | 001 | research agent | done | Primary sources; supported/partial/alternative/unsupported; no untested claims |
| W12-003 | Contained build feasibility and implementation | 001 | build agent | implemented; guest gates passed; ISO running | Runnable tooling; image writes isolated; verified inputs; fail closed |
| W12-004 | Desktop overlay and Office web integration | 002 | lead | implemented; runtime unverified | Runnable launchers, welcome/help, Windows-style desktop defaults |
| W12-005 | Integrate, build and validate milestone image | 003,004 | lead/build agent | active | Build logs/checksums; boot and install results or precise blockers |
| W12-006 | Release checkpoint and sync | 005 | lead | pending | Memory current; reviewed project-only commit synchronized |
| W12-007 | BIOS ISO evidence capture harness | 003,005 | research agent | implemented; unexecuted | Real contained ISO, screenshots/logs, new disposable disk only; no false success claim |
| W12-008 | Freeze release inputs and harden provenance | 005 | unassigned | pending | Snapshot repositories/input authentication; reproducibility records and repeat build |
| W12-009 | Windows application compatibility milestone | 005 | unassigned | pending | Choose maintained runtime; exact app/version functional tests and honest limits |
| W12-010 | Reliable interrupted-builder resume | 003 | unassigned | pending | Demonstrate interrupted long stage resumes with frozen source and refreshed proxy; current --resume is experimental |
