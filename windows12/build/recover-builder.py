#!/usr/bin/env python3
"""Guard one reboot recovery and quarantine stale live-build locks; never run lb.

Guest-only, explicit controller mode. Completed stages/caches/target are retained.
The parent selects the public post-bootstrap stages only after this exits0.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import stat
import sys
import time

BUILD = Path('/root/windows12-build')
OUT = Path('/project-output')
INSPECTOR = Path('/root/windows12-inspection.py')
VERSION = '1:20250505+deb13u1'
LIMIT = 256 * 1024
EMPTY_SHA = hashlib.sha256(b'').hexdigest()
RUNTIME = {'chroot_devpts', 'chroot_proc', 'chroot_selinuxfs', 'chroot_sysfs'}
BASE_FLAGS = {'config', 'bootstrap', 'bootstrap_cache.save', 'chroot_apt', 'chroot_debianchroot',
              'chroot_dpkg', 'chroot_hostname', 'chroot_hosts', 'chroot_resolv', 'chroot_sysv-rc'}
CONFIG = {
    'common': '441614d494379408f1eae97f4aafacc67759dc774487250ac90d1a34c8fc45d6',
    'bootstrap': 'a4bce96a1a100177de14a56ce567484b1583f01315e5d1cc4a34fc4a1cc64397',
    'chroot': 'cb6e2dd1c4fd0d08812e4925124a523594981afbc78fb329841f254c95b3ccc1',
    'binary': 'b16bcd609986cf369283406e68ab4e550acf7689788edb36e258bf7dc20b0a55',
    'source': 'b26d96ae9450d13e2df09e7729ee36c9d3f431b7c7c64d2066e6a13b8f2f0ff4',
}
FUNCTIONS = {
    'lockfile.sh': 'cacc640cdd247ed08db84c11e62b96015752b4848c34e5efc307d07581d9d880',
    'exit.sh': '7832fcf7b60660c1e64b8201d4257a7de7a0e12525205e8bd8cb7c8145fb67ff',
    'cache.sh': '977a54223a7c41593c551c8067f0c20e61d9e3e53ebed5889669a1761e3c4b3f',
    'stagefile.sh': 'aa66b2ec9f1443c8a7c39683bad778a3f5753a73e1af28fb14b0855152ce277f',
    'configuration.sh': 'e83601d40be86f5048198509d86cce5b031fdc53dc76a0b85087df1dde708a40',
}
SCRIPTS = {
    'build': '79d5b86f0c16b2ff060f8a8669eea214412dda481692d751c65d23480fc4717e',
    'bootstrap': 'f12a5e4e113cf85a0c96a1064e16e154c4c6d18a77f9af73fb9ff8e87e963b60',
    'bootstrap_cache': '299df8cc92f69e036c600eec599213a2e7deaff392dcab648255abc56e0b1f09',
    'chroot': 'abd9f5fae349d4e9a56300899861e12f891cdfb7abf44c5a4a203d6ea0ca8dd4',
    'chroot_prep': '98ccba668f5f69edd19aa28604d4d9e467554b3dc49b5a2ec99d452cd0530513',
    'chroot_cache': '7f9801543e735aba87fa66ebd4f906ebe8dd5d6eca90b229b32eb7c4b03f98e1',
    'chroot_tmpfs': '26f648a3e9a73ce74e30d14f6a443f33b172172545a56fd411ce03d40c020e47',
}
STATUS_SHA = '2fe156f9c72673a5cf03773f7773789b77050012ebf4cf2c1c26b635444ad4a7'
BASE_PACKAGES = {'apt', 'base-files', 'base-passwd', 'dpkg', 'libc6', 'systemd'}


def no_alias(path):
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Noncanonical guest recovery path')
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink():
            raise ValueError('Recovery symlink refused: ' + str(ancestor))
    return path


def read_regular(path, maximum):
    no_alias(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1 or info.st_size > maximum:
            raise ValueError('Unsafe recovery input: ' + str(path))
        data = stream.read(maximum + 1)
        if len(data) > maximum:
            raise ValueError('Oversized recovery input')
        after = os.fstat(stream.fileno())
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode, info.st_uid, info.st_gid, info.st_nlink) != (
                after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode, after.st_uid, after.st_gid, after.st_nlink):
            raise ValueError('Recovery input changed while read')
        return data


def sync_directory(path):
    fd = os.open(no_alias(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_report(report):
    payload = json.dumps(report, indent=2).encode() + b'\n'
    if len(payload) > LIMIT:
        raise ValueError('Recovery evidence exceeds256KiB')
    path = no_alias(OUT / 'builder-recovery.json')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1:
            raise ValueError('Unsafe recovery report destination')
        os.ftruncate(stream.fileno(), 0)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(OUT)


def valid_empty(item):
    return (item.get('exists') is True and item.get('type') == 'regular' and item.get('uid') == 0
            and item.get('gid') == 0 and item.get('links') == 1 and item.get('bytes') == 0
            and item.get('mode') == '0o644')


def validate(inventory, nonce):
    if (inventory.get('schema') != 1 or inventory.get('inspection_only') is not True
            or inventory.get('inspection_complete') is not True or inventory.get('inspection_nonce') != nonce
            or inventory.get('inspection_errors') or inventory.get('live_build_version') != VERSION
            or inventory.get('build_directory') != str(BUILD)):
        raise ValueError('Incomplete, stale or wrong-version inventory')
    uptime = float(inventory['uptime'].split()[0])
    if not 0 < uptime < 1800 or not re.fullmatch(r'[0-9a-f-]{36}', inventory['boot_id']):
        raise ValueError('Explicit fresh-boot inventory required')
    overrides = inventory['live_build_overrides']
    if overrides.get('environment_set') or overrides.get('environment_value') is not None or any(
            overrides[name].get('exists') is not False for name in
            ('local_override', 'empty_prefix_functions', 'empty_prefix_build_script')):
        raise ValueError('Live-build loader override refused')
    expected_sources = {str(Path('/usr/share/live/build/functions') / k): v for k, v in FUNCTIONS.items()}
    expected_sources.update({str(Path('/usr/lib/live/build') / k): v for k, v in SCRIPTS.items()})
    actual = {item['path']: item['sha256'] for item in inventory['source_functions']}
    if actual != expected_sources or len(actual) != len(inventory['source_functions']):
        raise ValueError('Installed live-build source hashes differ from reviewed source')
    actual_config = {Path(item['path']).name: item['sha256'] for item in inventory['config']}
    if actual_config != CONFIG or len(actual_config) != len(inventory['config']):
        raise ValueError('Saved configuration differs from approved inspection')
    expected_env = {'LB_CACHE': 'false', 'LB_CACHE_INDICES': 'false', 'LB_CACHE_PACKAGES': 'false',
                    'LB_CACHE_STAGES': 'bootstrap', 'LB_BUILD_WITH_TMPFS': 'false', 'LB_MODE': 'debian',
                    'LB_SYSTEM': 'live', 'LB_ARCHITECTURE': 'amd64', 'LB_DISTRIBUTION': 'trixie',
                    'LB_DISTRIBUTION_CHROOT': 'trixie', 'LB_DISTRIBUTION_BINARY': 'trixie', 'LB_DEBIAN_INSTALLER': 'live'}
    for key, value in expected_env.items():
        if key in os.environ and os.environ[key] != value:
            raise ValueError('Unexpected build environment override: ' + key)
    if os.environ.get('_FORCE') not in (None, '', 'false'):
        raise ValueError('Force-stage environment override refused')
    for name in ('config', 'build', 'chroot', 'installer', 'binary', 'source'):
        auto = no_alias(BUILD / 'auto' / name)
        if auto.exists():
            raise ValueError('Unreviewed auto-script override: ' + str(auto))
    stages = inventory['stage_flags']
    if not stages.get('exists') or stages.get('truncated'):
        raise ValueError('Complete stage inventory required')
    flags = {Path(item['path']).name: item for item in stages['entries']}
    if (len(flags) != stages['count'] or not BASE_FLAGS.issubset(flags)
            or set(flags) - BASE_FLAGS - RUNTIME or not all(valid_empty(item) for item in flags.values())):
        raise ValueError('Unexpected or unsafe stage state; do not fabricate completion flags')
    for name, item in flags.items():
        if item['path'] != str(BUILD / '.build' / name):
            raise ValueError('Unexpected stage path')
    database = inventory['chroot_dpkg']
    if database.get('status_sha256') != STATUS_SHA or database.get('status_counts') != {'install ok installed': 144}:
        raise ValueError('Target package database differs from inspected intact base')
    for name in BASE_PACKAGES:
        records = database['selected_packages'].get(name, [])
        if len(records) != 1 or records[0].get('Status') != 'install ok installed' or not records[0].get('Version'):
            raise ValueError('Target base package missing/incomplete: ' + name)
    if not inventory['chroot'].get('exists') or not inventory['bootstrap_cache'].get('exists'):
        raise ValueError('Retained target/bootstrap cache missing')
    process = inventory['active_build_package_processes']
    if process.get('matches') or process.get('truncated_at_64') or process.get('unreadable_pid_examples') or inventory['build_mounts']:
        raise ValueError('Active/unknown build processes or mounts; recovery refused')
    lock = inventory['lock']
    if lock.get('exists') and (not valid_empty(lock) or lock.get('content_prefix_hex') != ''):
        raise ValueError('Unexpected live-build lock; recovery refused')
    # matched configuration.sh defaults tmpfs to false when not saved; any
    # differing explicit config/environment is rejected above.
    return flags


def summary(inventory):
    names = ('boot_id', 'uptime', 'lock', 'stage_flags', 'config', 'source_functions', 'live_build_version',
             'live_build_overrides', 'chroot_dpkg', 'active_build_package_processes', 'build_mounts')
    value = {name: inventory[name] for name in names}
    for name in ('target_apt_archives', 'target_apt_partial', 'bootstrap_package_cache', 'bootstrap_cache', 'chroot'):
        value[name] = {key: item for key, item in inventory[name].items() if key != 'entries'}
    return value


def main():
    if not Path('/run/windows12-build-vm').is_file() or os.geteuid() != 0:
        raise SystemExit('Refusing host/non-root recovery; contained VM marker required')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nonce', required=True)
    parser.add_argument('--inspection-sha256', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{32}', args.nonce) or not re.fullmatch(r'[0-9a-f]{64}', args.inspection_sha256):
        parser.error('Expected nonce32hex and inspection-sha25664hex')
    no_alias(BUILD)
    if Path.cwd() != BUILD:
        raise SystemExit('Recovery must run from the fixed guest live-build directory')
    report = {'schema': 1, 'recovery_nonce': args.nonce, 'started': time.time(),
              'recovery_performed': False, 'resume_verified': False, 'outcome': 'preflight', 'quarantined': []}
    write_report(report)
    try:
        if hashlib.sha256(read_regular(INSPECTOR, 128 * 1024)).hexdigest() != args.inspection_sha256:
            raise ValueError('Inspection helper bytes differ from controller pin')
        namespace = runpy.run_path(str(INSPECTOR), run_name='windows12_recovery_inventory')
        if hashlib.sha256(read_regular(INSPECTOR, 128 * 1024)).hexdigest() != args.inspection_sha256:
            raise ValueError('Inspection helper changed while loaded')
        def inspect():
            previous = sys.argv
            try:
                sys.argv = [str(INSPECTOR), '--nonce', args.nonce]
                namespace['main']()
            finally:
                sys.argv = previous
            raw = read_regular(OUT / 'builder-inspection.json', LIMIT)
            value = json.loads(raw)
            validate(value, args.nonce)
            return value, hashlib.sha256(raw).hexdigest()
        before, before_sha = inspect()
        flags = validate(before, args.nonce)
        report.update(before=summary(before), before_inventory_sha256=before_sha,
                      inspection_helper_sha256=args.inspection_sha256)
        write_report(report)
        candidates = []
        if before['lock'].get('exists'):
            candidates.append((BUILD / '.lock', before['lock']))
        candidates.extend((BUILD / '.build' / name, flags[name]) for name in sorted(RUNTIME & set(flags)))
        if not candidates:
            raise ValueError('No stale recovery files found; do not replay this one-off recovery blindly')
        boot_ns = int((before['started'] - float(before['uptime'].split()[0])) * 1_000_000_000)
        if any(item['mtime_ns'] >= boot_ns - 5_000_000_000 for _, item in candidates):
            raise ValueError('Recovery file does not clearly predate this fresh boot')
        quarantine = no_alias(OUT / ('builder-recovery-quarantine-' + args.nonce))
        if quarantine.exists():
            raise ValueError('Recovery quarantine already exists; reconcile instead of repeating')
        quarantine.mkdir(mode=0o700)
        sync_directory(OUT)
        # Immediately refresh all conditions before the first mutation.
        immediate, _ = inspect()
        if summary(immediate) != summary(before):
            # uptime advances during inspection; compare substantive state below.
            left, right = summary(immediate), summary(before)
            left.pop('uptime'); right.pop('uptime')
            if left != right:
                raise ValueError('Builder state changed during recovery preflight')
        for path, expected in candidates:
            data = read_regular(path, 0)
            info = path.lstat()
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_uid, info.st_gid, info.st_nlink, stat.S_IMODE(info.st_mode)) != (
                    expected['device'], expected['inode'], 0, expected['mtime_ns'], 0, 0, 1, 0o644):
                raise ValueError('Recovery file changed immediately before quarantine')
            if info.st_dev != quarantine.stat().st_dev or hashlib.sha256(data).hexdigest() != EMPTY_SHA:
                raise ValueError('Unsafe cross-device or nonempty recovery file')
            target = no_alias(quarantine / path.name)
            if target.exists():
                raise ValueError('Quarantine target already exists')
            path.rename(target)
            sync_directory(path.parent)
            sync_directory(quarantine)
            report['quarantined'].append({'source': str(path), 'destination': str(target),
                                          'before': expected, 'sha256': EMPTY_SHA})
            write_report(report)
        after, after_sha = inspect()
        before_retained = {item['path']: item for item in before['stage_flags']['entries'] if Path(item['path']).name not in RUNTIME}
        after_retained = {item['path']: item for item in after['stage_flags']['entries']}
        if before_retained != after_retained or after['lock'].get('exists'):
            raise ValueError('Completed stages were not preserved or stale lock remains')
        for key in ('config', 'source_functions', 'chroot_dpkg', 'target_apt_archives', 'target_apt_partial',
                    'bootstrap_package_cache', 'bootstrap_cache', 'chroot'):
            if before[key] != after[key]:
                raise ValueError('Preserved builder state changed: ' + key)
        for moved in report['quarantined']:
            target = Path(moved['destination'])
            if hashlib.sha256(read_regular(target, 0)).hexdigest() != EMPTY_SHA:
                raise ValueError('Quarantined evidence changed')
            moved['after'] = namespace['metadata'](target)
        report.update(after=summary(after), after_inventory_sha256=after_sha,
                      recovery_performed=True, outcome='stale-files-quarantined-public-stages-required')
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        report.update(outcome='failed', error=str(error))
        return 1
    finally:
        report['finished'] = time.time()
        write_report(report)


if __name__ == '__main__':
    sys.exit(main())
