# Real ISO content audit — W12-019

Owner: `/root/boot_guard` (implementation); parent integrates, reviews and authorizes runtime. Assigned files: `scripts/audit-iso.py`, `scripts/build-tools.py`, this document only. All writable files remain within `/workspace/scratch/3c38ab731138/AI-use/windows12`. No VM, mount, host installation, global dependencies, root/sibling modification or Git mutation is assigned.

## Current task checkpoint

Implementation complete for parent review. Python AST syntax parsing and `git diff --check` passed. **No audit-tool preparation, actual ISO audit, extraction, runtime test suite or new VM was run during implementation.** The real ISO is still building. Source implementation is not a content-audit result.

The ISO bootstrap profile now requests `xorriso` and `squashfs-tools` through the existing signed-metadata resolver into its separate `iso-tools` directory. The VM profile and running QEMU tool tree are unchanged. Tool preparation will regenerate `build/iso-tools-lock.json`; the owner must review and checkpoint that changed lock separately.

Next concrete step: parent reviews the implementation, then authorizes the builder owner to prepare the separate tools and run the audit once a real completed ISO/checksum exists. Preserve resulting evidence and diagnose any strict-parser or content failure before claiming success. No current build disk or frozen archive needs changing.

## Invocation after review

From `AI-use/windows12`, with writable environment locations configured as in RUNBOOK.md:

```sh
python3 -B scripts/build-tools.py --profile iso
python3 -B scripts/audit-iso.py artifacts/vm-build/windows12-amd64-preview.iso \
  --source-archive .work/builder/checks.tar \
  --source-lock .work/builder/build-source.sha256 \
  --output artifacts/iso-audit-001
```

The output directory must be new. Inputs, tools, archives, locks and outputs must be regular files/directories under the project, without symlink path components. The ISO must have an ISO9660 signature and its digest must match either explicit `--sha256`, supplied `--checksum-file`, or the adjacent `SHA256SUMS`. If an adjacent checksum file exists it is checked even when an explicit digest is given. A checksum file must use strict GNU SHA256SUMS lines and contain exactly one digest for the actual ISO basename. This checks content consistency; it does not turn an unsigned generated checksum into release authentication.

`--source-archive` is mandatory. Its SHA256 must match a plain 64-hex source lock (default: sibling `build-source.sha256`). The audit reads overlay members and the package-version literal from that archive without extracting or executing source code. It never compares the ISO against newer working-tree overlay files. Keep the frozen source lock and provenance associated with the build; an operator-supplied lock alone is not independent origin authentication.

## Content gates

1. Match xorriso and unsquashfs executable bytes to their regular members in the cached `.deb` archives, and match those archives to SHA256 entries in the authenticated-bootstrap lock. `dpkg-deb --fsys-tarfile` decompresses into bounded memory; no package installation or maintainer script runs. This follows the existing installer-harness trust model: the lock and signed bootstrap validation are trusted records, not reverified signatures in the audit itself. The audit records executable/deb hashes and versions. Dynamic libraries are supplied by the same extracted tool closure but are not individually rehashed by this audit.
2. Record the actual ISO regular-file tree and El Torito report. Require `/live/filesystem.squashfs`, a live kernel/initrd listing, and at least one enabled El Torito boot-image entry. Those structures are prerequisites, **not a boot test**; neither BIOS nor UEFI success is certified from their presence.
3. Extract **only `/live/filesystem.squashfs`** to the new audit output. Require its little-endian SquashFS signature, record its digest and superblock report, then list it without extracting a guest root. No host mount, partition operation, guest executable or installer is invoked.
4. Read selected regular files using `unsquashfs -cat -no-wildcards`. Symlinks such as Debian's `/etc/os-release` are resolved entirely within the image listing, with bounded traversal and no host-path interpretation. Require Debian identity and exactly one `windows12-desktop` installed-status record at the version parsed from the frozen source packager. Also require installed records for the real KDE workspace/desktop, SDDM, Dolphin, Discover, Calamares/settings, Chromium, Firefox ESR, LibreOffice Writer/Calc/Impress, NetworkManager/Plasma integration, Python, xdg-utils and kernel meta-package listed in `CORE_PACKAGES`; record exact versions under `installed_core_package_versions`. These are package-presence checks, not functional certification.
5. Require every frozen overlay file to be listed in the package's installed file list and match its image bytes exactly. This includes the launchers, welcome help, desktop entries, Plasma defaults, copyright and wallpaper. Require managed paths to be regular files, reject world-writable overlay files, and require owner/group/other execute bits plus no group write on both launchers. Record modes and hashes. Require the help's independent Linux/partial/offline wording as a separate explicit gate.
6. Reject any listed known `windows12-build-proxy.crt` / `.pem` pathname or link target, and the exact known temporary APT proxy filename. Scan regular APT configuration files and `/etc/environment` for active proxy lines containing `10.0.2.2`, skipping full-line comments. APT directory aliases are refused for explicit follow-up rather than silently omitting their external subtree. This is a check for the project's known transient infrastructure, not a complete trust-store or credential-leak audit.
7. Confirm that the ISO and frozen source inode/size/mtime identity did not change during inspection. A concurrent input change invalidates the result. Do not audit a partial `.iso.part` or mutate the frozen input during inspection.

## Evidence, failure and limits

`result.json` defaults to `audit_passed: false`; only all successful gates set it true. It always leaves `boot_verified`, `install_verified` and `gui_verified` false. Errors and interruption retain the output and mark failure/interruption. Failures before a valid new output directory can be created print an error and create no result directory.

Retain `result.json`, `commands.jsonl`, numbered stderr logs, ISO file tree, El Torito report, extracted SquashFS, its listing/superblock report and target OS identity. The source archive and ISO remain inputs and are never overwritten. Large payloads and logs remain ignored artifacts. No arbitrary image path is extracted to a host path; the only image-file contents saved beyond the squashfs payload are fixed audit reports/OS identity.

Tool stdout is streamed with a bounded buffer and deadline, with strict nonzero-exit handling and process cleanup. Maximum selected-file reads are bounded; the full listing is limited to 128 MiB. Native parsers still process the image, so this tool is intended for the project's own checksum-matched builds, not as a sandbox for hostile images. The listing parser is deliberately strict and unexecuted against the eventual ISO: an unexpected tool format must fail visibly and be reviewed against real output, not silently treated as success.

The audit needs additional physical storage for a copy of the compressed live filesystem; it conservatively requires ISO size plus 256 MiB free before extraction. It does not delete builder disks/caches or run the synchronization-temp cleanup. Coordinate storage with the existing monitor and avoid running other inspection or test VMs concurrently.

This is an ISO content consistency check, not a malware scan, complete trust-store audit, actual boot test, installer certification or Windows compatibility test. After a successful audit, proceed to actual contained boot and disposable installation tests.

## Primary command basis

The squashfs-tools manual documents listing, `-cat`, no-wildcard selection, listing prefixes, numeric attributes and fatal/nonfatal exit codes: https://manpages.debian.org/trixie/squashfs-tools/unsquashfs.1.en.html . Exact compatibility with the authenticated Ubuntu tool version remains to be measured using the eventual real ISO. The xorriso listing/extraction pattern follows the existing project installer harness; no imaginary ISO result is supplied here.

## Prepared-tool evidence
After parent source review, build owner ran separate ISO tool prep69510, exit0 with signed metadata/index/archive checks. xorriso1.5.6 and unsquashfs4.6.1 startup succeeded; help confirmed listing/cat/prefix, bounded queue/processor and strict-error options. build/iso-tools-lock.json records xorriso1:1.5.6-1.1ubuntu3 and squashfs-tools1:4.6.1-1build1 plus dependencies. No real ISO extraction or audit was run; source-format/parser compatibility still needs the generated image. Main builder6329 and monitor82377 remained active and VM tools untouched. Logs are project-local under .work/builder and summarized in docs/RESTORED_BUILD.md.
