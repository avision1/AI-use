# Interrupted builder recovery evidence

Both root-owned31920/50947 handles became unknown; this alone was not treated as shutdown proof. Actual QMP reported no listener, runner.lock could be acquired exclusively, no build.exit or ISO existed. Last console reached bootstrap completion/target APT indexes (~1366s guest uptime), before desktop package download. Cause of host process loss is unknown; no guest success/failure exit was exported.

Offline `qemu-img check` found60 leaked clusters and explicitly described them as wasted space without harm to data. Original image was NOT repaired. Under the free runner lock, qemu-img convert created a new standalone qcow2; a new qemu-img check returned0. Original SHA was verified unchanged through conversion, then original disk/source/log/run record were preserved in `.work/failures/interrupted-2026-11-05/`. Replacement took the original expected project-local disk path only after clean check.

{
  "time": 1793922693.451602,
  "reason": "Supervisor/monitor handles vanished; runner lock free, QMP no listener, no exit marker; original60 leaked clusters",
  "original_sha256": "9fd24dd43e9f665dba46058f385aa41f5cabcade290c5a8d3427d6e202f50b2f",
  "original_disk": "/workspace/scratch/3c38ab731138/AI-use/windows12/.work/failures/interrupted-2026-11-05/build.qcow2",
  "replacement_sha256": "cb3cf08656a2e04fb030f5d144c2b530e9635aa7826b5e073887683f9b390169",
  "replacement_disk": "/workspace/scratch/3c38ab731138/AI-use/windows12/.work/builder/build.qcow2",
  "conversion": "qemu-img convert -f qcow2 -O qcow2, standalone new image; original unchanged",
  "new_qcow_check_returncode": 0,
  "guest_filesystem_verified": false,
  "source_sha256": "f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff"
}

This checks the qcow2 container, not the guest filesystem or staged live-build replay. Guest journal recovery and recipe rerun must be observed before claiming resume success. No host mount, partition, repair installer or global package operation occurred. Frozen source remains f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff. The next guarded --resume must refresh invocation proxy/seed and use this archive, never newer working source.

Queued validation77475 was canceled via its own output/cancel file and exited130 before any gate/test VM. Candidate output artifacts/candidate-gates-1793922586303757556 records interruption. No source-builder signal was sent. First rejected queue53349 and waiting-cancel operational run17006 also stopped. There is no active validation queue until explicitly recorded again after resume.

## Guarded resume active — latest authoritative jobs
Root-owned resume11322 and sole monitor86299 are now active. Guard reverified frozen source f045e04aff5ae2c730e171dc10b559655ad90724d62848c245b1b83ec8049dff; actual new Linux kernel boot observed from checked replacement disk. Invocation refreshed proxy/NoCloud seed. Log .work/resume-2026-11-05.log; serial.log appends both boots. Initial free60.38GB, disk1.930GB allocated, no sync copies. Guest journal/recipe replay still needs actual logs; do not claim staged recovery success yet. No active validation queue; old77475 canceled130, old53349 failed1 before gates. Requeue corrected validate-after-build.py only after confirming current resume record stable; no concurrent test VM.
