#!/usr/bin/env python3
"""Read-only inventory inside the contained builder; no build/repair actions.

The sole write is /project-output/builder-inspection.json inside the VM disk.
Do not execute on the host. Marker + controller VM isolation are both required.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time

BUILD = Path('/root/windows12-build')
OUTPUT = Path('/project-output/builder-inspection.json')
LIMIT = 256 * 1024


def no_alias(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Noncanonical guest path')
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError('Guest symlink refused: ' + str(part))
    return path


def read_regular(path, maximum):
    path = no_alias(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError('Not a bounded regular guest file: ' + str(path))
        data = stream.read(maximum + 1)
        if len(data) > maximum:
            raise ValueError('Guest file read exceeds bound: ' + str(path))
        after = os.fstat(stream.fileno())
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('Guest file changed while inspected: ' + str(path))
        return data


def metadata(path):
    # lstat records aliases without following/reading their destination.
    info = path.lstat()
    result = {'path': str(path), 'exists': True, 'mode': oct(stat.S_IMODE(info.st_mode)),
              'type': ('regular' if stat.S_ISREG(info.st_mode) else 'directory' if stat.S_ISDIR(info.st_mode)
                       else 'symlink' if stat.S_ISLNK(info.st_mode) else 'other'),
              'uid': info.st_uid, 'gid': info.st_gid, 'links': info.st_nlink,
              'bytes': info.st_size, 'device': info.st_dev, 'inode': info.st_ino,
              'mtime_ns': info.st_mtime_ns}
    if stat.S_ISLNK(info.st_mode):
        result['link_target'] = os.readlink(path)[:256]
    return result


def observe(path):
    no_alias(path.parent)
    try:
        return metadata(path)
    except FileNotFoundError:
        return {'path': str(path), 'exists': False}


def attempt(report, label, callback):
    try:
        return callback()
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        report['inspection_errors'].append({'item': label, 'error': str(error)[:512]})
        return None


def entries(directory, limit=512):
    no_alias(directory)
    if not directory.is_dir():
        return {'exists': False, 'entries': []}
    found = []
    count = 0
    deb_count = deb_bytes = 0
    with os.scandir(directory) as listing:
        for item in listing:
            count += 1
            info = item.stat(follow_symlinks=False)
            if item.name.endswith('.deb') and stat.S_ISREG(info.st_mode):
                deb_count += 1
                deb_bytes += info.st_size
            if len(found) < limit:
                found.append(metadata(directory / item.name))
    return {'exists': True, 'count': count, 'truncated': count > limit,
            'regular_deb_count': deb_count, 'regular_deb_bytes': deb_bytes,
            'entries': sorted(found, key=lambda item: item['path'])}


def package_summary(path):
    raw = read_regular(path, 32 * 1024 * 1024)
    data = raw.decode('utf-8', errors='replace')
    wanted = {'base-files', 'base-passwd', 'dpkg', 'apt', 'libc6', 'systemd', 'windows12-desktop',
              'plasma-desktop', 'plasma-workspace', 'sddm', 'calamares', 'chromium', 'libreoffice-writer'}
    counts, selected, incomplete = {}, {}, []
    for block in data.split('\n\n'):
        fields = {}
        for line in block.splitlines():
            if line.startswith(('Package: ', 'Version: ', 'Status: ')):
                key, value = line.split(': ', 1)
                fields[key] = value[:256]
        if not fields.get('Package'):
            continue
        status_value = fields.get('Status', '(missing)')
        counts[status_value] = counts.get(status_value, 0) + 1
        if fields['Package'] in wanted:
            selected.setdefault(fields['Package'], []).append(fields)
        if status_value != 'install ok installed' and len(incomplete) < 40:
            incomplete.append(fields)
    return {'status_sha256': hashlib.sha256(raw).hexdigest(),
            'status_counts': counts, 'selected_packages': selected,
            'noninstalled_examples': incomplete,
            'note': 'Database records only; no dpkg repair or application execution.'}


def processes():
    result = []
    unreadable = []
    names = {'lb', 'live-build', 'apt', 'apt-get', 'aptitude', 'dpkg', 'dpkg-deb', 'debootstrap'}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            data = read_regular(directory / 'cmdline', 65536)
        except (OSError, ValueError) as error:
            if len(unreadable) < 32:
                unreadable.append({'pid': int(directory.name), 'error': str(error)[:128]})
            continue
        arguments = [item.decode(errors='replace') for item in data.split(b'\0') if item]
        if not any(Path(item).name in names or item.startswith('/usr/lib/live/build/') for item in arguments):
            continue
        text = ' '.join(arguments)[:1024]
        text = re.sub(r'(?i)(https?://)[^/\s:@]+:[^/@\s]+@', r'\1[redacted]@', text)
        result.append({'pid': int(directory.name), 'command': text})
        if len(result) == 64:
            break
    return {'matches': result, 'truncated_at_64': len(result) == 64, 'unreadable_pid_examples': unreadable,
            'note': 'Point-in-time /proc scan, not proof of exclusive ownership.'}


def main():
    if not Path('/run/windows12-build-vm').is_file():
        raise SystemExit('Refusing host inspection: contained builder marker missing')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nonce', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{32}', args.nonce):
        parser.error('--nonce must be32 lowercase hexadecimal characters')
    no_alias(BUILD)
    report = {'schema': 1, 'started': time.time(), 'build_directory': str(BUILD),
              'inspection_only': True, 'inspection_nonce': args.nonce, 'inspection_complete': False,
              'cleanup_performed': False, 'resume_verified': False,
              'inspection_errors': []}
    report['boot_id'] = attempt(report, 'boot_id', lambda: read_regular(Path('/proc/sys/kernel/random/boot_id'), 128).decode().strip())
    report['uptime'] = attempt(report, 'uptime', lambda: read_regular(Path('/proc/uptime'), 128).decode().strip())
    lock = BUILD / '.lock'
    report['lock'] = attempt(report, '.lock lstat', lambda: observe(lock))
    if report['lock'] and report['lock'].get('type') == 'regular':
        report['lock']['content_prefix_hex'] = attempt(report, '.lock bounded content', lambda: read_regular(lock, 4096).hex())
    elif report['lock'] and report['lock']['exists']:
        report['inspection_errors'].append({'item': '.lock', 'error': 'Unexpected lock type; recorded without following it'})
    live_build = os.environ.get('LIVE_BUILD')
    report['live_build_overrides'] = {'environment_set': 'LIVE_BUILD' in os.environ,
                                     'environment_value': live_build,
                                     'local_override': attempt(report, 'local/live-build', lambda: observe(BUILD / 'local/live-build')),
                                     'empty_prefix_functions': attempt(report, '/functions', lambda: observe(Path('/functions'))),
                                     'empty_prefix_build_script': attempt(report, '/scripts/build.sh', lambda: observe(Path('/scripts/build.sh')))}
    if live_build is not None and len(live_build) > 4096:
        report['live_build_overrides']['environment_value'] = live_build[:4096]
        report['live_build_overrides']['environment_value_truncated'] = True
        report['inspection_errors'].append({'item': 'LIVE_BUILD', 'error': 'Environment override value exceeds4096 characters'})
    report['stage_flags'] = attempt(report, '.build', lambda: entries(BUILD / '.build'))
    report['config'] = []
    setting = re.compile(r'^(?:export\s+)?(?:LB_(?:CACHE\w*|BUILD_WITH_TMPFS|DISTRIBUTION\w*|ARCHITECTURE\w*|DEBIAN_INSTALLER\w*|MODE|SYSTEM)|APT_OPTIONS|LIVE_BUILD)=')
    for name in ('common', 'bootstrap', 'chroot', 'binary', 'source'):
        path = BUILD / 'config' / name
        data = attempt(report, str(path), lambda path=path: read_regular(path, 1024 * 1024))
        if data is not None:
            report['config'].append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                                     'settings': [line[:512] for line in data.decode(errors='replace').splitlines() if setting.match(line)][:64]})
    report['bootstrap_cache'] = attempt(report, 'cache/bootstrap', lambda: entries(BUILD / 'cache/bootstrap', 64))
    report['chroot'] = attempt(report, 'chroot', lambda: entries(BUILD / 'chroot', 64))
    report['chroot_dpkg'] = attempt(report, 'target dpkg/status', lambda: package_summary(BUILD / 'chroot/var/lib/dpkg/status'))
    report['target_apt_archives'] = attempt(report, 'target apt archives', lambda: entries(BUILD / 'chroot/var/cache/apt/archives', 256))
    report['target_apt_partial'] = attempt(report, 'target apt partial', lambda: entries(BUILD / 'chroot/var/cache/apt/archives/partial', 128))
    report['bootstrap_package_cache'] = attempt(report, 'bootstrap packages', lambda: entries(BUILD / 'cache/packages.bootstrap', 128))
    report['source_functions'] = []
    paths = [Path('/usr/share/live/build/functions') / name for name in ('lockfile.sh', 'exit.sh', 'cache.sh', 'stagefile.sh', 'configuration.sh')]
    paths += [Path('/usr/lib/live/build') / name for name in ('build', 'bootstrap', 'bootstrap_cache', 'chroot', 'chroot_prep', 'chroot_cache', 'chroot_tmpfs')]
    for path in paths:
        data = attempt(report, str(path), lambda path=path: read_regular(path, 2 * 1024 * 1024))
        if data is not None:
            report['source_functions'].append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()})
    env = {**os.environ, 'HOME': '/project-output', 'TMPDIR': '/project-output',
           'XDG_CACHE_HOME': '/project-output', 'XDG_CONFIG_HOME': '/project-output',
           'XDG_DATA_HOME': '/project-output', 'XDG_STATE_HOME': '/project-output', 'LC_ALL': 'C'}
    def version():
        value = subprocess.run(['dpkg-query', '-W', '-f=${Version}', 'live-build'], env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, check=True)
        return value.stdout.strip()[:128]
    report['live_build_version'] = attempt(report, 'live-build version', version)
    report['active_build_package_processes'] = attempt(report, 'process scan', processes)
    def numeric_mounts():
        text = read_regular(Path('/proc') / str(os.getpid()) / 'mountinfo', 1024 * 1024).decode(errors='replace')
        return [line[:1024] for line in text.splitlines() if len(line.split()) > 4 and
                line.split()[4].startswith(str(BUILD))][:128]
    report['build_mounts'] = attempt(report, 'mountinfo', numeric_mounts)
    report['finished'] = time.time()
    report['inspection_complete'] = not report['inspection_errors']
    payload = json.dumps(report, indent=2).encode() + b'\n'
    if len(payload) > LIMIT:
        raise SystemExit('Inspection report exceeds256KiB; refusing an incomplete inventory')
    no_alias(OUTPUT)
    if OUTPUT.exists():
        prior = OUTPUT.lstat()
        if not stat.S_ISREG(prior.st_mode) or prior.st_nlink != 1:
            raise SystemExit('Unsafe inspection output')
    fd = os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, 'wb') as destination:
        if not stat.S_ISREG(os.fstat(destination.fileno()).st_mode) or os.fstat(destination.fileno()).st_nlink != 1:
            raise SystemExit('Unsafe opened inspection output')
        os.ftruncate(destination.fileno(), 0)
        destination.write(payload)
        destination.flush()
        os.fsync(destination.fileno())
    print('Read-only builder inventory:', OUTPUT, '; errors:', len(report['inspection_errors']), '; no recovery performed', flush=True)


if __name__ == '__main__':
    main()
