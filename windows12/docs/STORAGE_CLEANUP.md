# Project storage cleanup — 2026-11-06

User-authorized cleanup reclaimed **10.34 GiB** from obsolete disposable disks and an extracted duplicate. The sole actual QEMU opened only the new clockfix disk and pinned cloud backing image. Every removed path was a regular single-link project file, unchanged at unlink and not open by QEMU. Logs, run/results, frozen source, original ISO and authenticated inputs remain.

| Removed path | Allocated bytes |
|---|---|
| `artifacts/install-serial20-001/disposable-install.qcow2` | 8102875136 |
| `artifacts/candidate-gates-1793950554450406600/audit/filesystem.squashfs` | 2770030592 |
| `.work/interrupted-before-live-build-1793950417375223518/build.qcow2` | 62857216 |
| `artifacts/overlay-check-196e24e1e16eef4083a3ff138c4ab309/check.qcow2` | 24387584 |
| `artifacts/overlay-check-1c5ce6050a112c056f393ef804426e5e/check.qcow2` | 23994368 |
| `artifacts/overlay-check-2e5f15f759bd4fbc5a770de8f78cd814/check.qcow2` | 23207936 |
| `artifacts/overlay-check-5c78814e281bf549335a6647bffc1de9/check.qcow2` | 23207936 |
| `artifacts/overlay-check-af7aacea0e12491fe6b08b7615d9a464/check.qcow2` | 200704 |
| `artifacts/overlay-check-c11fb30393c6f70b20f9472002912b2f/check.qcow2` | 22814720 |
| `artifacts/overlay-check-c1a753df3961007c2a70d9abc089842c/check.qcow2` | 22159360 |
| `artifacts/overlay-check-cab87aa07f654e7123fe1234a8e50838/check.qcow2` | 23207936 |

The failed late-verification disk was superseded by the successful passstdout installation. Cloud-check children were stopped/independent; the interrupted pre-build child had no retained target. The duplicate SquashFS is reproducible from the retained ISO and has recorded audit SHA256f186a6f4a0c7a399e085460a162b5d5e3750e4c7860d3015c75b891f6d2d60cc.

Keep authenticated tool/package/index caches and pinned cloud input to avoid downloading them repeatedly. Keep active builder and successful baselines needed for near-term validation. After the corrected ISO passes installation/desktop/reboot acceptance, review the old completed builder, superseded baselines and old ISO for retirement, preserving original signed inputs and compact evidence first. Do not retain large obsolete builds without an explicit next use.

Detailed original stat/removal record: `.work/storage-cleanup-1793996702435125858.json`. No unrelated device files were touched.
