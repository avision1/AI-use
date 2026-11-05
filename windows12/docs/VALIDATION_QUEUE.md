# Sequential post-build validation

Run once from windows12 after an existing build has recorded its frozen source and run.json:

```bash
python3 -B scripts/validate-after-build.py --install
```

The queue waits up to4hours for that exact builder's build.exit0 and released runner.lock. It does not stop/restart/control the builder. Changing the run record, source lock or gate scripts causes refusal. Every output is in a new artifacts/candidate-gates-<timestamp> directory, including project-local HOME/TMP/XDG directories. Existing gate tools enforce their own VM lock and legacy-QMP checks; the queue never starts guests concurrently.

After real source digest/ISO checks, it invokes audit-iso.py against the frozen archive, BIOS screenshot collection for300seconds, and (with --install) install-test.py on a NEW disposable disk. Audit must pass. ISO stat identity and gate-controller hashes remain fixed across stages; each VM result's ISO SHA256 must equal the actual audited ISO digest. BIOS captures must exist, be contained regular files, and have P6 headers. The installed proof additionally needs the one-shot proof field. A failure stops further gates and preserves evidence.

Content audit, BIOS evidence collection and installed-root boot proof are separate booleans. GUI and release certification always remain false. Review screenshots manually and perform interactive live/installed account, application and update workflows; Calamares is a separate test. A completed capture is never a boot/desktop pass, and an installed-root marker is never a login/Office/Windows compatibility pass.

## Cancellation and recovery

Create the file `cancel` in the exact queue output directory to cancel only that queue. Waiting cancellation is noticed within30seconds. During a helper stage it sends only the owned helper SIGINT and allows45seconds for its own VM cleanup. SIGTERM to the queue uses the same cooperative path. It never kills a helper directly, signals the source builder, auto-resumes CPUs, reuses a disk, publishes artifacts, or changes host partitions.

If the helper cannot stop or exits from a signal, active_helper and helper_reconciliation_required remain in the report and no next gate starts. Reconcile its recorded command/PID, runner lock and QMP controls before restarting anything; force-killed controllers cannot guarantee VM cleanup. A nonzero helper exit is not a passed gate. Logs and result.json are in the queue output; exceptions before a usable output path may only appear in supervising output.

--wait-timeout accepts60–14400seconds and bounds only the waiting phase. Audit and VM helpers have their own stage timeouts. Time expiration leaves the builder untouched. Do not alter gate scripts or build metadata while this controller is waiting unless deliberately canceling that run; use a new explicit queue/output after reviewing replacements.

## Evidence status

Independent source review identified interruption and candidate-identity issues, corrected before any actual gate launch. See VALIDATION_QUEUE_REVIEW.md. AST syntax checks passed. A real waiting/cancel operational check passed (job17006, queue returned130, builder run record unchanged, no helper/test VM launched; .work/validation-queue-cancel-check.json); actual content/BIOS/install and helper-interruption branches require the completed ISO and are not certified by source review. The rejected first queue53349 exited1 after an audit-only run-record cancellation event; no helper/test VM launched and the builder's command/disk/source/proxy fields stayed unchanged. Future normal cancellation uses the queue's own cancel file.
