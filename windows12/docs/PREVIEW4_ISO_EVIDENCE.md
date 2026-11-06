# Preview4 ISO evidence — 2026-11-06

An actual hybrid amd64 ISO exists at `artifacts/vm-build/windows12-amd64-preview.iso` (ignored generated output; not uploaded to Git).

- Size: 3,579,805,696 bytes.
- SHA256: `7d36b5847fba7240ee2795bb42ff3ea841652569b7eb983cfec6ea96968ae11c`.
- Frozen source archive SHA256: `027051ef7e6da1be12cabb3664a06ce5be0801a307acfc89bd7cb2dfa288b6e9`.
- Build exit: 0; builder stopped. Source/provenance/logs and adjacent SHA256SUMS retained in `.work/builder/` and `artifacts/vm-build/`.
- Base: Debian13 amd64; desktop package0.1.0~preview4.

## Measured validation

`artifacts/candidate-gates-1793950554450406600/audit/result.json` passed the checksum/content audit against frozen source. It verified managed file hashes/modes, required Plasma/SDDM/Calamares/LibreOffice/browser packages, independent Linux help, and absence of known transient build proxy/CA files. El Torito lists bootable BIOS and UEFI entries; structure is not runtime UEFI proof.

BIOS capture reached the ISO boot menu. Independently reviewed original screenshot: `artifacts/candidate-gates-1793950554450406600/bios/screen-0010.ppm`. It shows Live system, fail-safe, and installer options; no key was sent by the capture-only harness. This proves a BIOS boot menu, not a running desktop.

The first automated D-I test stopped before partitioning with `WRONG_DISK_GUARD`; no installation was certified. Evidence: `artifacts/candidate-gates-1793950554450406600/install/`. Its harness generated a27-byte serial; virtio-blk exposes20bytes. The fix limits the disk ID to `W12` +17hex characters while keeping the full24hex token for callbacks/installed-boot proof, and updates the GUI provenance reader. The exact single-disk/name/serial guard remains enforced.

Primary serial-limit implementation references: https://raw.githubusercontent.com/qemu/qemu/v8.2.0/hw/block/virtio-blk.c (GET_ID) and https://raw.githubusercontent.com/torvalds/linux/v6.12/include/uapi/linux/virtio_blk.h (VIRTIO_BLK_ID_BYTES).

The corrected controllers passed all52 tests in the disposable guest, deterministic double packaging and dpkg inspection; guest shutdown confirmed. Evidence: `artifacts/overlay-check-5c78814e281bf549335a6647bffc1de9/`, source SHA256 `3ab2bd35eb5c9269b48f65f34a67455fc8bd211f5dd3b416782e3f0d14192524`. This host-only harness fix does not alter the existing ISO.

## Remaining acceptance

Fresh corrected D-I installation and ISO-free installed-root proof; live Plasma login/workflows; installed desktop login/workflows; separate Calamares installation; UEFI/Secure Boot and physical hardware coverage. Do not recommend replacing an existing computer OS based only on the successful content audit and boot menu. No physical disk operation has been performed.

Keep the ISO, checksum manifest, original authenticated inputs, tool archives/locks, frozen source, package manifest and full logs independently preserved. Git preserves source/memory rather than these ignored generated artifacts.
