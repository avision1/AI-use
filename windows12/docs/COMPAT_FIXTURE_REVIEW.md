# Fixture acquisition source review — 2026-11-05

Owner: `/root/fixture_review_nov05`. Scope: `scripts/compat-fixtures.py`, `build/compat-fixtures.lock.json` and `docs/COMPAT_FIXTURES.md`. Read-only source review; only this document was written. No project module import, test suite, download, signature command, Windows execution, VM/QMP action or Git mutation was performed. Current builder31920/monitor50947 were untouched. All work remains under `/workspace/scratch/3c38ab731138/AI-use/windows12/`.

No blocking defect was established for the checked-in four-fixture lock. The implementation checks contained non-symlink paths, regular single-link files, exact size/SHA256, bounded HTTPS-only downloads and the required Notepad++ signature against an exact primary fingerprint. The report correctly leaves compatibility/application execution false and does not claim a signature for the unsigned 7-Zip cases. The parent's reported real download, signature, offline and altered-byte checks were not repeated by this reviewer.

## Evidence-reporting issue resolved in source

The original `main()` validated the lock and created environment directories before constructing the report/entering its `try/finally`. A later preflight failure could therefore leave the preceding `verification.json` success unchanged. This was a low-severity evidence-reporting issue, not an execution or signature-verification bypass.

The lead added `write_report()` and a false `input-validation-incomplete` report before lock preflight for verification invocations. Source review confirms that lock parse/schema/path and environment-directory failures now leave an incomplete false record when the report destination is usable. Final verification writes `verified` or `failed`. `--list` intentionally preserves verification evidence because it is not a verification invocation. If the report path itself is unsafe/unwritable, it cannot be safely replaced; the nonzero CLI exit remains authoritative. No new source blocker was identified.

The parent reports job73615 exited0: a preserved cached7-Zip file was temporarily absent, `--verify-only` exited unsuccessfully and `verification.json` recorded `hash_verification_passed=false`. The exact file was restored in cleanup and the subsequent offline pin/signature run passed. Evidence: `.work/compat/missing-cache-negative-check.json`. This operational check exercises acquisition failure/report invalidation; the earlier preflight case is established by source review, not a separately claimed malformed-lock runtime test.

## Remaining evidence

- Publisher-key raw-origin verification is now parent-measured: HTTPS download reproduced exactly34929 bytes and SHA256 `40d6de423a3c0025c4ce9d23a2b8cc8ef5c265b8f74bdc52e149783a080ea4db`. Evidence: `.work/compat/key-origin-fetch.log` and `npp-key-origin.asc`. This reviewer did not execute the fetch. The separate origin check closes the raw-byte reproduction uncertainty; it is not an additional Windows execution result.
- Application/runtime support remains wholly untested by this downloader. Bottles setup, separate x64/x86/MSI workflows, save/reopen/archive integrity, uninstall and offline operation still need the contained graphical guest tests already specified in WINDOWS_APP_RUNTIME_PLAN.md.

No generic host-security or Windows compatibility certification is inferred from this source review.
