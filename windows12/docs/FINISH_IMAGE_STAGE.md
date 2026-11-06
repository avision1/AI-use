# Completing the retained image after public chroot

Status: exact-source continuation design; no finishing helper or controller mode is implemented by this change. No VM, helper, package installer, target executable or network operation was run. The live chroot transaction is not complete yet. This document must not be treated as an ISO or installation result.

## Public stage order

The authenticated retained source is `live-build_20250505+deb13u1.tar.xz`, SHA256 `1aad324e433d6cb6d038193252b74fd0ed1c1e1d7e1c6cf410c8fb09c5225b9e`. Its `scripts/build/build` invokes bootstrap, chroot, installer, binary and source in that order. Once the actual package-stage proof establishes chroot completion, the remaining public calls are:

```text
/usr/bin/lb installer
/usr/bin/lb binary
/usr/bin/lb source
```

These are guest-only commands for the existing frozen build directory, not instructions to run on the host. A future controller must retain only the frozen VM guard/log/export/shutdown prefix, then invoke a separately pinned finishing helper. It must not retain the original test/package/configuration setup or call `lb build`, `lb bootstrap`, `lb chroot`, `lb config`, `lb clean` or `--force`. `lb source` itself exits without generating a source image when the actual effective `LB_SOURCE` is not true; do not invent a source-stage completion flag.

## Why a finishing wrapper is not ready

The first 1,946-archive manifest plans only the live target's package installation transaction. It does not authorize or authenticate every remaining installer and binary-stage input.

| Exact source | Important behavior | Consequence |
| --- | --- | --- |
| `installer_chroot`, lines 56–59 | Moves the completed live tree to a nested location and copies `cache/bootstrap` into a temporary installer chroot | The retained bootstrap cache becomes executable input; its earlier shallow metadata inventory is insufficient for this boundary |
| `installer_debian-installer`, lines 61–73 | Requires wget, apt-utils and appstream, installs dependencies, runs target apt-get update | The current live-target archive plan does not cover the temporary install environment |
| Same, lines 201–227 and 373–411 | Uses a URL-derived file cache and wget for D-I kernel/initrd, plus GTK variants when selected | Size/existence-based cached reuse must not be presented as authenticated input verification |
| Same, lines 413 onward | Resolves BIOS/UEFI/Calamares, filesystem and firmware packages and generates installer pools | Fresh authenticated selection/provenance is needed for the selected effective configuration |
| `binary_chroot`, lines 67–74 | May copy bootstrap and move the completed live tree into a temporary binary chroot | Failure can leave a nested/transitional tree; blind continuation or root-status checks against the wrong location are unsafe |
| `binary_rootfs`, lines 265–271 | Installs squashfs-tools for the configured compressed root | A full live desktop package cache is not a complete binary-tool transaction |
| `binary_iso`, lines 50–65 | Resolves xorriso, isolinux, optional grub-pc-bin and optional isomd5sum | More stage-specific build inputs are required |

The exact native network path must be authorized before any acquisition. The parent's last download session reported a policy block for `https://deb.debian.org:443`; do not retry through alternate origins, mirrors, proxy settings or unsigned inputs to evade it. This review performed no request and does not establish whether the restriction is temporary. Source work and read-only evidence work can continue independently.

The private `APT_OPTIONS=... --no-download` overlay belongs to the preceding public chroot mode. Reusing it here without complete additional stage inputs will fail and still does not control wget, metadata updates or arbitrary hooks. Dropping it silently would also change the recorded acquisition contract. The finishing mode needs its own explicit, reviewed input policy and effective configuration probe.

## Finishing-helper preflight contract

1. The host controller holds the existing runner lock and reconciles QMP ownership. It validates the frozen `checks.tar` against its source lock and the source identity associated with the actual successful chroot run. All disks, inputs and outputs remain project-contained.
2. A fresh guest VM marker, fixed guest root/CWD, fresh nonce, and controller-supplied SHA256 pins bind the finishing helper and its reviewed prerequisite-reader bytes. The predecessor `package-stage-result.json` SHA256 and nonce must be supplied explicitly, rather than accepting the latest file by name alone.
3. Require predecessor schema 1, `chroot_completed=true`, public-chroot return code 0, `iso_verified=false`, final quiescence/runtime flags absent, and a valid complete installed-manifest record. Rehash `package-stage.packages` against its recorded size/SHA256, and rehash the actual live target status against `installed_manifest.target_status_sha256`. Reject ambiguous JSON, aliases, unexpected links, changed inputs or incomplete output.
4. Recheck the exact pinned installed live-build frontend/loader/functions/scripts and the complete effective configuration order. Re-read the five saved config hashes. Verify no auto scripts, environment/loader overrides or local implementation overrides. Recheck the effective architecture, distribution, image type, build-with-chroot, bootloaders, installer GUI, source, cache and firmware options. Do not rely on an old pure-configuration probe from the preceding mode.
5. Require exact recorded completed-stage inventory, no live target mounts, no active package/build process and absent build lock. Refuse any installer/binary/source stage already present, `chroot.tmp`, `chroot/chroot`, installer-cache marker or partial image tree until a separate actual-state recovery decision is reviewed. Never clear flags or discard partial directories automatically.
6. Establish a full authenticated inventory of the bootstrap cache before it becomes the temporary executable environment. Validate merged-/usr symlinks through a narrowly reviewed target-aware inventory, not a generic recursive host resolve. Preserve its original bytes. The previously recorded shallow bootstrap-cache evidence explicitly cannot satisfy this gate.
7. Plan the installer/binary acquisition closure from the actual effective configuration and exact source, or explicitly document ordinary native authenticated acquisition with the authorized network path. Include build-tool DEBs, installer pools/firmware and D-I non-DEB inputs. Authenticate and pin each applicable input through its actual upstream signature/checksum chain; preserve any assurance gap honestly. Normal APT signatures do not authenticate arbitrary wget bodies by themselves.
8. Require enough guest and host space for the completed live tree, temporary bootstrap tree, compressed filesystem, installer pools and exported ISO together. Existing 24 GiB virtual disk capacity is not proof of enough free space. Record measured guest free bytes before each expensive public stage and host free bytes before export.

Only after these gates should the finishing helper invoke public stages sequentially. Keep bounded streamed child logs, exact return codes, command/source/config identities and a fresh result checkpoint. A failure preserves all partial trees and flags and requires read-only inventory before retry. The helper must never claim chroot, installer or binary success from a marker alone.

## Output and controller integration

On successful `installer`, `binary` and the configured `source` behavior, require no target mounts or active build/package process and preserve actual final stage inventory. The expected source recipe outputs are `live-image-amd64.hybrid.iso` and `live-image-amd64.packages` in `/root/windows12-build`. Validate them as bounded regular output files with reviewed link/ancestry handling, reject preexisting destination output, and retain the generated originals. Export distinct copies under `/project-output/windows12-amd64-preview.iso` and `/project-output/windows12-amd64-preview.packages` with size and streaming SHA256 records. Write SHA256SUMS only after complete successful copies and fsync. Record the exact frozen source identity and package-stage predecessor identity alongside new finishing provenance.

The host mode must use a fresh `artifacts/image-finish-*` output directory and explicit allowlisted uploads for the finishing report, package manifest, ISO and SHA256SUMS. It must validate task return code, fresh nonce/provenance, nonempty ISO and actual host-received hashes independently. No global `artifacts/vm-build` success marker may be borrowed from an earlier mode. The existing validation queue currently assumes its own build output lifecycle, so either integrate the new finishing result deliberately or call content/boot/install tools explicitly against the newly verified ISO.

A successful exported ISO is ready for inspection, not certified for use. Follow with authenticated ISO content audit against the frozen source, BIOS/live desktop test, disposable-disk installer and ISO-free reboot, then Calamares/installed desktop, Office and Windows-app workflows. UEFI and hardware testing remain distinct evidence. The result must retain separate booleans for image creation, content audit, live boot, installed boot and graphical/application validation.

## Source evidence pins

| Archive member beneath `live-build/` | SHA256 |
| --- | --- |
| `scripts/build/build` | `79d5b86f0c16b2ff060f8a8669eea214412dda481692d751c65d23480fc4717e` |
| `scripts/build/installer` | `9fc5b0e50b3a4030ef69260d5a088e3097a8e0f732b7c50d54a675aa81fdf81c` |
| `scripts/build/installer_chroot` | `723cb6ba4cdcb3ea45e06a70936b10847b2196d52e61335bd3df4a1b8d26ee90` |
| `scripts/build/installer_debian-installer` | `20a23b6625e3cbd7f38f28fc36d78dd664ec3ca1d82041e221d2ce90c78afd0b` |
| `scripts/build/binary` | `386136aab20e27cf9b87dfa605c1d729b031a840334349f044a83cc5d1bcab50` |
| `scripts/build/binary_chroot` | `aeabd4229122630ebdf5a9b3a91817ba28d2f07758a83dfd61c7d5106f6df8ac` |
| `scripts/build/binary_rootfs` | `e6498a5c69ea21660005854ee37c6a5634a9a8448ed5e32a308b647318e2f12b` |
| `scripts/build/binary_iso` | `396a68c7d86d1b660a493d9d307fcd53dfee3cfafcbb9840779a4a2742b99959` |
| `scripts/build/source` | `c4ea4653b851acb56cef5cd0089ff475ffc481afabf5829d1023729a1be5c9fd` |

Validation: read-only archive inspection and line/hash extraction of the exact retained source; read existing guest recipe and offline stage implementation/report shape; Markdown whitespace check. No runtime claim. `build/finish-image-stage.py` was intentionally not created because the prerequisite completed chroot proof and additional input/trust inventory do not exist yet; a runnable success path would outrun available evidence.
