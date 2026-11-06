# Reboot-only live-build lock recovery research — 2026-11-05

Owner `/root/fixture_review_nov05`; owned files are this document, `build/inspect-builder.py` and `.work/lock-review/`. Strict sole host project boundary `/workspace/scratch/3c38ab731138/AI-use/windows12/`. No host installation, guest/VM/QMP action, cleanup, source-build mutation or Git operation was performed. The helper is for later parent-controlled execution only inside a full contained VM; no runtime validation is claimed here.

## Exact reviewed source

Parent reports actual guest package `live-build1:20250505+deb13u1`. Official source downloaded into `.work/lock-review/` from https://deb.debian.org/debian/pool/main/l/live-build/live-build_20250505+deb13u1.tar.xz . SHA256 matches the supplied pin exactly: `1aad324e433d6cb6d038193252b74fd0ed1c1e1d7e1c6cf410c8fb09c5225b9e`. This fetch is HTTPS plus the independently supplied fixed digest; this review did not verify a Debian source-package signature. Reviewed archive members were read, and selected exact member bytes were saved only under the owned work directory for hashes/line references.

| Source member | SHA256 |
|---|---|
| functions/lockfile.sh | cacc640cdd247ed08db84c11e62b96015752b4848c34e5efc307d07581d9d880 |
| functions/exit.sh | 7832fcf7b60660c1e64b8201d4257a7de7a0e12525205e8bd8cb7c8145fb67ff |
| functions/cache.sh | 977a54223a7c41593c551c8067f0c20e61d9e3e53ebed5889669a1761e3c4b3f |
| scripts/build/bootstrap | f12a5e4e113cf85a0c96a1064e16e154c4c6d18a77f9af73fb9ff8e87e963b60 |
| scripts/build/bootstrap_cache | 299df8cc92f69e036c600eec599213a2e7deaff392dcab648255abc56e0b1f09 |
| scripts/build/chroot | abd9f5fae349d4e9a56300899861e12f891cdfb7abf44c5a4a203d6ea0ca8dd4 |
| scripts/build/chroot_prep | 98ccba668f5f69edd19aa28604d4d9e467554b3dc49b5a2ec99d452cd0530513 |
| scripts/build/chroot_cache | 7f9801543e735aba87fa66ebd4f906ebe8dd5d6eca90b229b32eb7c4b03f98e1 |
| scripts/build/chroot_tmpfs | 26f648a3e9a73ce74e30d14f6a443f33b172172545a56fd411ce03d40c020e47 |
| scripts/build/build | 79d5b86f0c16b2ff060f8a8669eea214412dda481692d751c65d23480fc4717e |

Installed functions normally reside under `/usr/share/live/build/functions/`; installed build scripts under `/usr/lib/live/build/` (upstream Makefile43,51–52). Guest inventory should hash the installed bytes rather than relying on version text alone. Unset `LIVE_BUILD` and absence of `local/live-build` must be established, because `scripts/build.sh` permits local function/script overrides.

## Lock semantics

`Acquire_lockfile()` defaults to `.lock` in the current live-build working directory, here guest `/root/windows12-build/.lock` (`lockfile.sh12–17`). `Check_lockfile()` merely checks whether it is a regular file and exits1 with PROGRAM already locked (19–27). It does not inspect PID, boot identity or contents. `Create_lockfile()` installs a removal trap for EXIT/HUP/INT/QUIT/TERM and uses `touch` (29–39). A normally created lock is therefore an empty file; abrupt emulator loss/power loss can preserve it without a live owner. Empty content alone does not prove staleness.

Minimal candidate cleanup is only that exact `.lock`, after fresh-boot/exclusive-owner evidence, installed source/version matching, and a zero-byte regular root-owned single-link non-symlink file check. Record path/stat/inode/content evidence before removing it. Reject unexpected type/content/aliases, active live-build/APT/dpkg/debootstrap work or unknown mounts. Do not apply this deletion automatically during an ordinary running build. It belongs only inside an explicitly selected recovery boot of the stopped contained disk.

## Why lock deletion plus lb build is unsafe for preserved progress

The `bootstrap` script always calls `bootstrap_cache restore`, then debootstrap, then cache save. If `cache/bootstrap` exists and `.build/bootstrap_cache.restore` is absent, restore passes its stage check, acquires `.lock`, then **removes the current chroot** before copying the bootstrap cache (`bootstrap_cache38–69`). This occurs even if `.build/bootstrap` already exists. Thus merely clearing `.lock` and replaying `lb build` can discard retained desktop downloads/packages/configuration. Do not fabricate a completed restore flag to suppress this path.

There is a second loss risk: `bootstrap` sets `Setup_clean_exit`; on failure, `Exit()` unmounts helpers, removes four runtime-prep flags and calls `Save_package_cache` (`exit.sh24–64`). With `LB_CACHE=false`, that cache helper removes target `chroot/var/cache/apt/archives/*.deb`. The failed resumed disk may therefore have already purged downloads despite failing at the stale lock. This is a source-derived possibility; actual cache counts must come from inventory. Preserve the original interrupted disk separately and do not assume the failed resumed copy has equivalent cached work.

## Proposed recovery selection; not executed

First run the parent's read-only inspection mode; do not call `lb`, cleanup or repair while collecting evidence. Require a confirmed new guest boot with exclusive controller/runner ownership, no prior build processes/mounts, exact source/configuration, real `.build/config` and `.build/bootstrap` completion markers, intact retained chroot/base dpkg database and evidence of the interrupted stage. Require effective `LB_CACHE=false`/bootstrap-only stage caching and `LB_BUILD_WITH_TMPFS=false`; the tmpfs mode moves the dpkg database into volatile RAM and is not safely recoverable by simply clearing mount flags.

If completed bootstrap and intact target are proven, the public remaining pipeline is `lb chroot`, `lb installer`, `lb binary`, `lb source`, in that order, without force. Those are precisely stages2–5 from `scripts/build/build54–67`; this avoids re-entering destructive bootstrap restoration and preserves completed package/installer/binary flags. `lb chroot` recreates its own package/file manifests normally. This is a proposed version-specific continuation, not a measured successful resume.

After a reboot, four mount-preparation flags can outlive their mounts: `.build/chroot_devpts`, `.build/chroot_proc`, `.build/chroot_selinuxfs`, `.build/chroot_sysfs`. Upstream `Exit()` removes exactly these. If present with no corresponding current mounts, parent may implement a separately logged exact allowlist reconciliation so public prep helpers mount them again; do not erase `.build`, completed package stage markers, installer flags or caches. If these conditions are not proven, stop and inspect rather than apply a generic clean/rebuild or `--force`.

`build/inspect-builder.py` is source-ready for parent review. It requires the VM marker and `--nonce <32-lowercase-hex>`; reports `schema:1`, `inspection_only:true`, matching `inspection_nonce`, and `inspection_complete:true` only if all requested inventory reads completed without inspection errors. Errors remain explicit in the report; missing optional cache directories are recorded as absent. Parent must check this nonce/contract rather than accept an old report from the retained guest disk. No cleanup success or resume success is inferred.

It records lock lstat/bounded contents, stage metadata, configuration hashes/relevant literal settings, retained cache/chroot/target dpkg summary, exact `.deb` counts/bytes plus bounded filenames, installed source-function hashes, `dpkg-query` live-build version, point-in-time active build/package command lines and relevant current mounts. A missing `.lock` is a valid `exists:false` observation, not an inspection error; an unexpected present lock type is recorded and errors. It explicitly records whether `LIVE_BUILD` is set and its exact value (an oversized value is marked truncated/incomplete), lstat/absence of build-root `local/live-build`, and the `/functions` and `/scripts/build.sh` fallback-prefix locations that the upstream loader can check when the variable is empty. No override is sourced or executed. These observations let the parent reject an unexpected loader override rather than trust only the installed-package hashes.

The helper never executes lb/APT/dpkg repair, chroot, mount or removal commands. Process scans explicitly report unreadable/truncated cases and do not prove exclusive ownership. Source paths are fixed and aliases refused; reads use bounded nonblocking no-follow descriptors. Output JSON is capped256KiB, and the sole write is `/project-output/builder-inspection.json` inside the contained VM disk after non-symlink/regular/single-link checks.

Host AST syntax validation passed; the helper was not imported or executed on the host. Parent owns wrapper embedding, nonce/helper-hash provenance, export allowlisting and the actual inspection boot. No recovery action has been executed by this agent. After receiving actual inventory, select a narrowly guarded continuation or stop for further diagnosis; this document does not authorize blind lock or stage-file deletion.
