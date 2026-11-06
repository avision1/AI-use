# Inspection wrapper source review — 2026-11-05

Owner `/root/inspect_wrapper_review`. Scope is the new `--resume --inspect-resume` path in `scripts/build-vm.py`, the actual frozen shell prefix in `.work/builder/checks.tar`, and the inventory helper's report contract. All work/read-only review and this sole owned document remain within `/workspace/scratch/3c38ab731138/AI-use/windows12/`. No host project import, runtime suite, VM/QMP command, package install, mount, source modification or Git mutation was performed.

No source-proven route was found from inspection mode into the full tests/package/APT/live-build recipe or an ISO-success claim. The existing shared runner lock and legacy-QMP launch refusal are unchanged. The explicit argument combination requires an existing resumed disk, and the source archive digest is checked before its shell prefix is used. The exact frozen prefix ends after the tee/export/EXIT-shutdown setup, before the unique `mkdir -p /root/windows12-checks` boundary. Separate `artifacts/builder-inspect-<timestamp>` output preserves the ordinary `artifacts/vm-build` failure artifacts. The host inspection branch returns before the normal ISO-success gate and prints an explicit no-ISO-success statement.

## Findings resolved in wrapper source

1. The helper is now read once as bytes; its SHA256 and decoded embedded text derive from that same buffer. The potential provenance race from two reads is resolved.
2. The wrapper now generates a fresh32-hex-character nonce, passes it as `--nonce` to the embedded Python helper, and records it with helper SHA256 in run.json. Host acceptance requires a dictionary with schema1, inspection_only=true, inspection_complete=true and that exact nonce. This closes acceptance of arbitrary JSON/retained prior report as a fresh inventory. The final helper must implement that exact argument/report contract; the final helper implements the matching --nonce/schema/complete contract and was reviewed by the lead. A mismatch fails the host gate rather than certifying inspection.
3. Documentation follow-up resolved: wrapper docstring now includes separate inspection outputs.

No remaining wrapper source blocker was identified after these changes, subject to final helper-contract agreement. Requiring cleanup_performed=false/resume_verified=false as additional report assertions would make the intended non-recovery contract more explicit; the reviewed guest code still provides the substantive no-cleanup boundary, and metadata is not independent attestation.

Inspection mode is a normal writable guest boot: cloud-init, certificate refresh, journal recovery, logs and the report can write inside its contained VM disk. “Read-only inventory” should mean no build-tree cleanup/repair, not that the disk is opened read-only. The helper and frozen shell export prefix still require actual guest execution/export/clean-shutdown verification before inspection is considered measured. Runtime absence of build activity and any later stale-lock recovery are separate gates, never inferred from this source review.

Parent integration also requires cleanup_performed=false/resume_verified=false and refuses a symlinked received report. Generated guest shell passes bash -n and both Python files pass AST parsing. Actual guest inventory/export remains pending.
