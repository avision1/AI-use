# Security-upgraded package-stage recovery

Source-only review, 2026-11-06. Runtime validation and delivery are pending. No inspector, recovery helper, package installation, VM command, project module or host test suite was executed for this change.

The explicit `--package-stage` mode in `build/inspect-builder.py` and `build/recover-builder.py` selects the named `temporary-live-build-security-upgraded-package-stage-os-release-diversion` profile. Ordinary modes keep the original bootstrap status/checksum pins and lifecycle requirements. The new profile is limited to the actual interrupted package-download stage recorded in `artifacts/builder-inspect-1793928271552577785/builder-inspection.json`; it is not a generic package recovery or integrity exception.

## Exact approved state

- Package status: 144 `install ok installed`, SHA256 `cf0bdc5bd7e2c0332cb2906f099c044077321f6583fc4eb45eac7d452b2c91e8`.
- Stored MD5 metadata: 144 files, 450161 bytes, aggregate SHA256 `1dfcd7999383a91e54e9cec6729910adcabde8b22f102c81294a239bcfc8bb76`.
- Required completed flags: original ten (`config`, `bootstrap`, `bootstrap_cache.save`, `chroot_apt`, `chroot_debianchroot`, `chroot_dpkg`, `chroot_hostname`, `chroot_hosts`, `chroot_resolv`, `chroot_sysv-rc`) plus `chroot_archives`, `chroot_firmware`, `chroot_includes_before_packages`, `chroot_linux-image`, `chroot_package-lists.install`, `chroot_preseed`.
- Only a subset of existing runtime preparation flags `chroot_devpts`, `chroot_proc`, `chroot_selinuxfs`, `chroot_sysfs` may accompany those sixteen. Actual inventory has nineteen: required sixteen plus devpts/proc/sysfs. After quarantine it must retain exactly sixteen. Completed package-install/hacks flags or any other extra flag fail.
- The native verifier must complete with return0, sole stdout `missing     /etc/os-release.debootstrap` plus newline, empty stderr, and no truncation. Raw findings and `available_md5_no_reported_differences=false` remain unchanged.
- All original exact authentic vendor os-release, complete derived identity, valid UTC build timestamp, local no-rename diversion and genuinely absent backup checks remain mandatory. See `docs/TARGET_VERIFY_REVIEW.md` for the exact source explanation and coverage limits. No file is repaired, synthesized or broadly ignored.

Recovery requires the explicit named accepted classification and exact new status/checksum facts, plus all fourteen installed live-build source pins, five configuration pins, VM/root/fresh boot/nonce/helper pin checks, no unknown active processes or mounts, no force/loader/auto-script overrides and existing safety checks. `--package-stage` cannot combine with `--refresh-target-indexes`. Its only quarantine candidates are the existing stale empty `.lock` and allowed runtime preparation flags. It preserves completed flags, status/database, archives/partial/cache and APT index inventories. Empty candidate selection still refuses. The report explicitly records `package_stage=true`; it does not invoke live-build or assert successful resume.

## Source-proven no-download option propagation

Reviewed exact live-build `1:20250505+deb13u1` archive `.work/lock-review/live-build_20250505+deb13u1.tar.xz`, SHA256 `1aad324e433d6cb6d038193252b74fd0ed1c1e1d7e1c6cf410c8fb09c5225b9e`. Read-only extracts and individual SHA256 hashes are preserved under `.work/package-stage-review/`, with manifest `source-review.json`.

**Plain `APT_OPTIONS='... --no-download' lb chroot` is insufficient for this target.** Actual `config/common` explicitly assigns `APT_OPTIONS="--yes -o Acquire::Retries=5"`. `functions/init.sh:Init_config_data` calls `Read_conffiles` before `Prepare_config`; saved configuration overwrites that environment value. `configuration.sh:120` defaults with `${APT_OPTIONS:---yes -o Acquire::Retries=5}` only afterward. No supported `--apt-options` switch was found in the reviewed argument handling.

The exact supported configuration-selection mechanism is exported `LB_CONFIG`, read by `functions/conffile.sh:Get_conffiles`. A controller can preserve the complete normal configuration read order and append one final controller-pinned, guest-only options file containing only:

```sh
APT_OPTIONS="--yes -o Acquire::Retries=5 --no-download"
```

The list must include the six standard files `config/all config/common config/bootstrap config/chroot config/binary config/source`, then their usual `.amd64` and `.trixie` variants in the order produced by `Get_conffiles`, then that final absolute options-file path. `LB_CONFIG` explicitly replaces the standard list; omitting a normally read file would change semantics and is not approved by this review. Files absent in the standard sequence remain absent. Verify the list and every existing config/variant/environment input, require no later overrides, and pin the final options file before launch; do not alter target resolver config, target APT config, the five saved configs or installed live-build sources. This is a proposed controller-bound option overlay, not an implemented delivery mechanism in these helpers.

Source propagation:

1. `frontend/lb` executes the chosen public script through `/usr/bin/env` without clearing the inherited environment, after loading `config/environment` and `config/environment.binary` assignments. Those assignments must not override the reviewed selector/options.
2. Each public helper calls `Init_config_data`; the final selected file reasserts `--no-download` after the saved common assignment. `Prepare_config` retains nonempty APT_OPTIONS. Color handling appends only its APT color option.
3. Public `scripts/build/chroot:44` calls `lb chroot_install-packages` for install/live passes. The exported selector remains inherited by nested `lb` processes.
4. `chroot_install-packages:88` expands `${APT_OPTIONS}` directly into the `xargs ... apt-get ... install` command before entering `Chroot`. `functions/chroot.sh` clears the target environment with `env -i`, but the option is already an argument in the command; target environment inheritance is unnecessary.

This proves option transport from reviewed source, not offline success or network isolation. `--no-download` applies to apt-get package acquisition; it does not prohibit every network operation by live-build, hooks or maintainer scripts. Native contained APT verification against the complete authenticated pinned package plan/cache and a fresh guarded recovery are still required. Full continuation and ISO/boot gates remain pending.

## Validation completed here

Both changed Python files parse with `ast.parse`. The existing JSON was read without executing project modules: required sixteen flags are present, only devpts/proc/sysfs remain beyond them, and exact new status/checksum/native finding facts match the new pins. All other classification and recovery branches received source review only. No runtime acceptance, preservation, offline installation or build success is claimed.
