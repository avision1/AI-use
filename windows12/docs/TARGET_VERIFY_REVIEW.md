# Read-only target payload verification review

Owner `/root/inspect_wrapper_review`; source research only. All writes/downloads are confined to `/workspace/scratch/3c38ab731138/AI-use/windows12/docs/TARGET_VERIFY_REVIEW.md` and `.work/verify-review/`. No VM/QMP/Git action, project module import, host runtime test, target command, repair or package installation was performed.

## Recommendation

Add a bounded read-only inspection action using the **trusted builder's** dpkg, not a chroot execution of the target binary:

```text
/usr/bin/dpkg --root=/root/windows12-build/chroot --verify-format=rpm --verify
```

Record the actual builder dpkg version, full command, return code, bounded stdout/stderr, elapsed time and whether the timeout/output bound was reached. Keep ordinary package/status inventory alongside it. Do not add install/configure/reinstall, trigger-processing, force, or repair options. Invoke this only inside the contained guest, with the inspector's existing process/mount/quiescence checks and project-output environment.

**A zero return code is insufficient.** In exact dpkg1.22.22 source, verify_package reports path failures but returns void; verify returns0 unless an explicitly named package is not installed. Missing paths, changed digests and unexpected file types can therefore be printed while the command returns0. Treat any stdout as differences requiring classification, any stderr/error as incomplete or review-needed, and any timeout/output truncation as incomplete. Only a completed bounded invocation with no reported differences/errors can be described as no differences reported for the checked metadata. Do not turn that statement into an unconditional filesystem-integrity pass.

## Exact read-only semantics

The versioned primary manual identifies1.22.22. It defines --root as selecting both installation directory and its var/lib/dpkg database. --verify compares file content with stored MD5 information where present; its format must be selected explicitly for stable parsing. This is an integrity screen, not publisher authentication or security verification. Missing checksum metadata means missing coverage. The nine-character result can report a digest/type issue or missing path; a trailing c identifies a conffile, not an automatically acceptable difference.

Exact source adds the operational details important here:

- src/main/verify.c opens the package database read-only, loads diversions, loads package file/hash metadata and reads installed paths. It does not call package installation/configuration or maintainer-script machinery. src/main/main.c excludes the verify action from invoke-hook actions, so ordinary pre/post invocation hooks are not run for this action.
- lib/dpkg/dbmodify.c does not acquire its writable database lock, rewrite status/updates, checkpoint or save available data for that read-only mode. A function named cleanupdates still reads outstanding database updates; its write/unlink branch is guarded by writable mode. Do not infer that its name performs a repair here.
- This is root-prefix path lookup, not execution inside the target root. Some pathname symlinks can resolve into the builder guest filesystem; unexpected type/path results must not be ignored. No host filesystem is shared with this guest. A wall timeout remains necessary for unreadable/special or unexpectedly large payload cases.
- Status144 installed and a matching status-file SHA alone do not establish payload bytes, checksum metadata completeness, permissions, bootability or usable applications. MD5 screening can detect accidental changes such as zeroed content when an intact expected digest exists; it cannot establish all files or authenticate a potentially altered local database.

## Live-build preparation and diversions

Reviewed exact live-build1:20250505+deb13u1 chroot_dpkg and chroot_sysv-rc source, already hash-pinned in project recovery research:

| Prepared path/state | Source behavior | Verification interpretation |
|---|---|---|
| usr/sbin/start-stop-daemon | Local diversion preserves the packaged executable at a diversion destination, then the original path becomes an absolute /bin/true symlink. A merged-usr compatibility diversion also covers the sbin spelling. | Do not expect a digest/type failure merely from seeing the intentional wrapper. Dpkg verification resolves the diversion destination before inspecting the pathname. Inventory the actual diversions and inspect/hash the preserved original separately. |
| usr/sbin/policy-rc.d | Existing path, if any, is diverted; live-build creates a shell script that denies runlevel operations with exit101. | A newly generated unowned wrapper is outside package checksum coverage. If a packaged original was diverted, check that preserved original explicitly. No blanket exception for arbitrary policy-file differences. |
| usr/sbin/flash-kernel | Local diversion plus /bin/true wrapper; the original may not exist in this amd64 base. | Package verification has no coverage for an unowned generated file. Classify against actual installed ownership/diversion state, not filename alone. |
| etc/dpkg/dpkg.cfg.d/live-build and .live-build marker | Live-build adds its unsafe-io preparation config and generic marker; cleanup later removes them. | Added unowned files need explicit source-intent inventory; dpkg --verify need not report them. This proposed check does not enable unsafe-io or execute dpkg package actions. |

There is an additional subtle coverage limit for diverted originals in this exact verifier. src/main/help.c selects the destination node via namenodetouse; it does not transfer a digest from the original node. lib/dpkg/db-fsys-digest.c attaches loaded MD5 entries to their listed names, and verify_file only hashes the selected node when that node has a digest. Thus absence of a report is **not proof that a diverted backup received an MD5 check**. For start-stop-daemon, supplement the screen by reading the original package MD5 entry and comparing it explicitly with the corresponding preserved executable, while requiring its expected regular-file type. For stronger assurance, compare against the exact authenticated dpkg binary-package payload instead of trusting only the target's own metadata. No such comparison was executed by this research task.

The applicable backup name is determined by actual diversion records, not a guessed .distrib filename: the source includes merged-usr compatibility handling and can use start-stop-daemon.distrib.usr-is-merged or the usr/sbin .distrib path. Do not run a target script or automatically restore/remove these wrappers to make verification quiet. Do not broadly ignore conffile-tagged differences; explain each against known build preparation or retain it as unresolved.

## Primary evidence and preserved research

- Exact manual: https://manpages.debian.org/trixie/dpkg/dpkg.1.en.html , version1.22.22, sections --verify, --root, --verify-format and invocation hooks. Reviewed source behavior is more specific than the generic return-status summary.
- Exact official source archive: https://deb.debian.org/debian/pool/main/d/dpkg/dpkg_1.22.22.tar.xz . Saved only beneath .work/verify-review.5746724bytes, SHA256 d5ea9f132deec8030b50ab2a02ade2b49f0c7a195805a302c8301156fe833a57. This research used official HTTPS plus recorded hash; an independent source-archive signature chain was not verified.
- Source hashes: verify.c c76ab2b9b703f969a1715ee4693bca32baf3fa7bca13ab8b2a3ad4f616277b79; help.c bcf84c6983fa2c7e43bda360f387c1b4dd254df9586800611df735bfccd20ef1; main.c bd5e4759d09545f408213f59751c1421fb004d899aa1b81c6ba89a7e113ab2fe; dbmodify.c b12cc4fc7985a790744953773e76cc6be4ed8ce2a0de83ae3e00aef9bf0d3026; db-fsys-digest.c 0dca2045f1ad3305129de636f7f3c59aeb4b3c7b10ceae276e985f05a771e20b.
- Exact live-build archive and source context: docs/LIVE_BUILD_LOCK_RECOVERY.md and project-local .work/lock-review/live-build_20250505+deb13u1.tar.xz; chroot_dpkg and chroot_sysv-rc were read directly from that archive without execution.

This review does not assert that target payloads are corrupted. The parent's zero-prefixed APT index findings concern reproducible indexes; this separate screen can establish additional payload evidence before cache recovery, with the limits above. It remains an optional proposed inspection check until implemented and actually run by the parent.

## Inspector integration source review

The parent implemented target_payload_verification in build/inspect-builder.py and requested source-only integration review. It invokes the builder's absolute dpkg path with explicit target root and rpm format, uses a120-second timeout, and records command/return code/stdout/stderr plus a stored-md5 metadata count, size and aggregate SHA256. Metadata reads are individually bounded and have a16MiB aggregate bound. Report text is capped at32768 stdout and8192 stderr characters and marks truncation; the subprocess currently captures its output before applying those report caps. No output-memory hard bound is claimed by this review.

The available_md5_no_reported_differences flag requires return0, nonempty checksum coverage, no reported stdout/stderr and no truncation. A timeout/read error is captured as an inspection error and cannot pass recovery validation. recover-builder.py requires that flag before selecting or mutating recovery candidates, with no automatic path/conffile ignore list. The coverage text preserves the local-diversion/available-MD5 limitations. This addresses the exact1.22.22 return-code trap; it does not certify diverted original backups or every payload file.

No source-proven blocker was found in this integration for the currently approved base. An actual reported difference/unknown result is expected to stop the next attempt for review rather than be suppressed. No verifier command or recovery operation was executed by this reviewer; actual target integrity evidence remains pending.

## Exact os-release.debootstrap finding after the guarded attempt

The parent reports refresh48889 stopped before quarantine. Its fresh verifier returned0 with the sole line `missing     /etc/os-release.debootstrap`, no stderr and144 stored MD5 files/450161bytes (metadata aggregate SHA2567a8db8eeb27715739965b9ebab51089dcec46205552c2a7b816476cc9f630487). This is a reported missing path, not an MD5 mismatch. It must remain visible in the raw report and the no-reported-differences flag remains false.

Exact live-build1:20250505+deb13u1 explains a candidate legitimate transient state. scripts/build/bootstrap_debootstrap125–141, after debootstrap itself completes, adds a local diversion from /etc/os-release to /etc/os-release.debootstrap using no-rename. It then removes the original etc symlink, copies usr/lib/os-release into etc/os-release and appends the live image ID/build timestamp. No-rename deliberately does not create the diversion destination. The verifier subsequently resolves the original package path through this diversion and can report the intentionally absent destination. The literal diversion filename does not occur in regular payload files of the exact debootstrap1.0.141 package read for this review; the creator is live-build's bootstrap wrapper.

The exact chroot stage runs package installation passes before chroot_hacks. That script62–65 removes this diversion, again without renaming, once package installation is done. It does not restore the etc symlink or move a backup into place. Therefore the diversion is temporary build state, not something to silently carry into a final installed root. Debian bug1111039 identifies this cleanup fix as present in this exact live-build release: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1111039 . Do not apply old installation repair snippets to the incomplete builder merely to quiet verification.

### Precise read-only evidence before classifying this one line

- Require this exact reviewed live-build mode/version and source hashes, existing completed bootstrap flag, absent chroot_hacks completion, and the approved ten-flag/package-status/config snapshot. Do not accept the same missing line for an arbitrary completed image or installed system.
- Read the actual target diversions file without executing a target program. Require exactly the local triple for /etc/os-release, /etc/os-release.debootstrap and the local marker `:`; reject another destination, package-specific owner or ambiguity.
- Observe the backup with lstat semantics: genuinely absent, not a dangling alias, arbitrary file or directory. Inspect current etc/os-release and usr/lib/os-release as bounded non-symlink regular root-owned files.
- Authenticate the usr file against exact base-files13.8+deb13u7 package bytes:286bytes, MD5 `776b0aac9b17d49a0ac879da9801f51b`, SHA256 `e249e69c32d81350fdd6b05ac5575255f14e380ba14b8454acea14e49f088bfa`. Its package metadata lists that MD5 for usr/lib/os-release and its packaged etc/os-release is the relative symlink ../usr/lib/os-release.
- Require the entire current etc file to equal those authentic286bytes followed by only `IMAGE_ID=live` plus newline, then `BUILD_ID=` plus a16-character valid UTC timestamp in YYYYMMDDTHHMMSSZ format plus newline:326bytes total, no other lines or bytes. This trixie branch does not apply the separate sid/unstable substitutions. Preserve observed bytes/hashes/timestamp in the report.
- Require the verifier's sole exact missing-path line, empty stderr, return0, complete untruncated invocation and unchanged approved checksum-metadata digest; any other finding remains unexplained and aborts. If all evidence matches, record a separate narrowly justified no-unexplained-differences classification. Do not change no-reported-differences to true, invent the missing backup, remove the diversion during preflight, or broaden an ignore list.

### Preserved exact reference inputs

Both binary packages were downloaded under .work/verify-review and matched the existing authenticated Debian Packages index pins before read-only archive inspection. No package was installed and no maintainer script was executed.

- debootstrap1.0.141 all.deb:50094bytes, SHA2568c02cb8ad712eb67afb0d23fab175c562804cc97eda70b70cb0f3bc2a21732d7; official URL https://deb.debian.org/debian/pool/main/d/debootstrap/debootstrap_1.0.141_all.deb .
- base-files13.8+deb13u7 amd64.deb:88296bytes, SHA256fcd42bb5cb63f7bfc4326a92541247872206d60a192fdff65ca14eb83ed408b9; official URL https://deb.debian.org/debian/pool/main/b/base-files/base-files_13.8+deb13u7_amd64.deb . Reference usr/lib/os-release bytes are preserved at .work/verify-review/base-files-reference-os-release. Its postinst was inspected as text and does not create this os-release.debootstrap diversion.
- Reviewed live-build bootstrap_debootstrap SHA2560397f1e77a01f82d83cbf479cf63954c1eb138c8cbba721247f93b03341db8a3; chroot_hacks SHA2561dac3a0aee51d35119aa649cf3001faac31dbbe940cc847fe8d4695033607dc9. Require matching installed scripts before relying on these precise preparation/cleanup semantics.

These are source/reference facts and proposed inspection predicates. The target's current path/diversion/reference-byte agreement has not been executed or established by this reviewer. The parent owns a fresh read-only inspection before any guard classification or recovery. Final image/installed-root diversion cleanup and release identity remain separate actual validation gates.

Arithmetic correction: the derived os-release size is326bytes, not325:286 reference bytes +14bytes for IMAGE_ID=live/newline +9bytes BUILD_ID= +16timestamp bytes +1newline. The authoritative predicate is equality with exactly constructed bytes; a size check alone is insufficient.
