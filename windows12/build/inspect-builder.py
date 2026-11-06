#!/usr/bin/env python3
"""Read-only inventory inside the contained builder; no build/repair actions.

The sole write is /project-output/builder-inspection.json inside the VM disk.
Do not execute on the host. Marker + controller VM isolation are both required.
"""
import argparse
import datetime
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


def apt_index(path):
    item = observe(path)
    if not item['exists']:
        return item
    if item['type'] != 'regular':
        raise ValueError('Unexpected target APT index type; not followed: ' + str(path))
    raw = read_regular(path, 64 * 1024 * 1024)
    item.update(sha256=hashlib.sha256(raw).hexdigest(), header_hex=raw[:64].hex(),
                content_read_bound_bytes=64 * 1024 * 1024)
    return item


def diversion_inventory():
    path = BUILD / 'chroot/var/lib/dpkg/diversions'
    item = observe(path)
    if not item['exists']:
        return {**item, 'raw_text': None, 'triples': [], 'parse_complete': True}
    if item['type'] != 'regular' or item['uid'] != 0 or item['links'] != 1:
        raise ValueError('Unsafe target diversions metadata; no content followed')
    raw = read_regular(path, 64 * 1024)
    try:
        text = raw.decode('utf-8')
        valid_utf8 = True
    except UnicodeError:
        text = raw.decode('utf-8', errors='replace')
        valid_utf8 = False
    lines = text.splitlines()
    count = len(lines) // 3
    triples = [{'path': lines[i], 'diverted_to': lines[i + 1], 'package': lines[i + 2]}
               for i in range(0, min(count, 128) * 3, 3)] if valid_utf8 else []
    return {**item, 'sha256': hashlib.sha256(raw).hexdigest(), 'raw_text': text,
            'raw_utf8_valid': valid_utf8, 'raw_prefix_hex': raw[:256].hex(),
            'triples': triples, 'triple_count': count, 'triples_truncated': count > 128,
            'unparsed_line_count': len(lines) % 3,
            'parse_complete': valid_utf8 and len(lines) % 3 == 0 and count <= 128}


def image_os_release(literal):
    root = no_alias(BUILD / 'chroot')
    allowed = {'/etc/os-release', '/etc/os-release.debootstrap', '/usr/lib/os-release'}
    if literal not in allowed:
        raise ValueError('Unapproved os-release inspection path')
    initial = root / literal.lstrip('/')
    result = {'image_path': literal, 'lstat': observe(initial), 'link_steps': []}
    if not result['lstat']['exists']:
        result['resolution'] = 'absent'
        return result
    def normal(parts):
        resolved = []
        for part in parts:
            if part in ('', '.'):
                continue
            if part == '..':
                if not resolved:
                    raise ValueError('Relative symlink escapes target image')
                resolved.pop()
            else:
                resolved.append(part)
        return resolved
    parts = normal(literal.split('/'))
    for _ in range(17):
        prefix = []
        changed = False
        for index, part in enumerate(parts):
            candidate = root.joinpath(*prefix, part)
            item = observe(candidate)
            if not item['exists']:
                result.update(resolution='missing-link-target', unresolved_image_path='/' + '/'.join(parts))
                return result
            if item['type'] == 'symlink':
                target = os.readlink(candidate)
                result['link_steps'].append({'image_path': '/' + '/'.join(prefix + [part]),
                                             'target_literal': target[:4096], 'target_truncated': len(target) > 4096})
                if target.startswith('/'):
                    result['resolution'] = 'unsupported-absolute-symlink-not-followed'
                    return result
                if len(target) > 4096:
                    result['resolution'] = 'unsupported-oversized-symlink-not-followed'
                    return result
                try:
                    parts = normal(prefix + target.split('/') + parts[index + 1:])
                except ValueError:
                    result['resolution'] = 'unsupported-relative-symlink-escape-not-followed'
                    return result
                changed = True
                break
            prefix.append(part)
        if changed:
            continue
        resolved_literal = '/' + '/'.join(parts)
        resolved = root.joinpath(*parts)
        if not resolved.is_relative_to(root) or resolved_literal not in allowed:
            result.update(resolution='unsupported-target-outside-exact-os-release-set',
                          resolved_image_path=resolved_literal)
            return result
        final = observe(resolved)
        result.update(resolved_image_path=resolved_literal, resolved_lstat=final)
        if final.get('type') != 'regular':
            result['resolution'] = 'unsupported-nonregular-target-not-read'
            return result
        raw = read_regular(resolved, 16 * 1024)
        result.update(resolution='image-contained-regular', sha256=hashlib.sha256(raw).hexdigest(),
                      md5=hashlib.md5(raw, usedforsecurity=False).hexdigest(), content_bytes=len(raw),
                      content_bound_bytes=16 * 1024)
        try:
            result['content_utf8'] = raw.decode('utf-8')
        except UnicodeError:
            result['content_utf8'] = None
            result['content_hex'] = raw.hex()
        return result
    result['resolution'] = 'unsupported-symlink-chain-limit'
    return result


def base_files_os_release_md5sums():
    path = BUILD / 'chroot/var/lib/dpkg/info/base-files.md5sums'
    item = observe(path)
    if not item['exists'] or item['type'] != 'regular' or item['uid'] != 0 or item['links'] != 1:
        raise ValueError('Expected bounded root-owned base-files checksum metadata')
    raw = read_regular(path, 2 * 1024 * 1024)
    matches = []
    malformed = 0
    for line in raw.decode('utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{32})[ \t]+(.+)', line)
        if not match:
            malformed += 1
            continue
        filename = match[2].removeprefix('*').removeprefix('./')
        if filename in ('etc/os-release', 'etc/os-release.debootstrap', 'usr/lib/os-release'):
            matches.append({'path': filename, 'expected_md5': match[1], 'raw_line': line})
    return {**item, 'sha256': hashlib.sha256(raw).hexdigest(), 'matches': matches,
            'malformed_line_count': malformed,
            'note': 'Stored expected MD5 only; no classification, security verification or diversion repair.'}



def classify_payload(report):
    """Classify one source-proven construction state; never suppress raw output."""
    payload = report.get('target_payload_verification')
    if not isinstance(payload, dict):
        return
    payload['available_md5_no_unexplained_differences'] = payload['available_md5_no_reported_differences']
    result = {'accepted': False, 'kind': 'temporary-live-build-os-release-diversion',
              'reason': 'No temporary-state exception established',
              'coverage': 'Available MD5 screen plus exact os-release evidence only; not all-file/security verification.'}
    payload['temporary_preparation_classification'] = result
    if payload['available_md5_no_reported_differences']:
        result['reason'] = 'Native verifier reported no differences; no temporary-state exception used'
        return

    def require(condition, reason):
        if not condition:
            raise ValueError(reason)

    def regular(item):
        return (isinstance(item, dict) and item.get('exists') is True and item.get('type') == 'regular'
                and item.get('uid') == 0 and item.get('gid') == 0 and item.get('links') == 1
                and item.get('mode') == '0o644')

    try:
        require(payload.get('returncode') == 0 and payload.get('stdout') == 'missing     /etc/os-release.debootstrap\n'
                and payload.get('stderr') == '' and payload.get('output_truncated') is False,
                'Native verifier findings do not match the sole reviewed missing backup')
        require(payload.get('stored_md5_file_count') == 144 and payload.get('stored_md5_metadata_bytes') == 450161
                and payload.get('stored_md5_metadata_sha256') == '7a8db8eeb27715739965b9ebab51089dcec46205552c2a7b816476cc9f630487',
                'Stored checksum metadata differs from the reviewed bootstrap')
        require(report.get('live_build_version') == '1:20250505+deb13u1', 'Unreviewed live-build version')
        sources = {item['path']: item['sha256'] for item in report['source_functions']}
        require(sources.get('/usr/lib/live/build/bootstrap_debootstrap') == '0397f1e77a01f82d83cbf479cf63954c1eb138c8cbba721247f93b03341db8a3'
                and sources.get('/usr/lib/live/build/chroot_hacks') == '1dac3a0aee51d35119aa649cf3001faac31dbbe940cc847fe8d4695033607dc9',
                'Installed preparation/cleanup source differs from reviewed source')
        packages = report['chroot_dpkg']
        require(packages.get('status_sha256') == '2fe156f9c72673a5cf03773f7773789b77050012ebf4cf2c1c26b635444ad4a7'
                and packages.get('status_counts') == {'install ok installed': 144}
                and packages['selected_packages']['base-files'] == [{'Package': 'base-files', 'Version': '13.8+deb13u7', 'Status': 'install ok installed'}],
                'Target package database/version is not the approved bootstrap')
        stages = report['stage_flags']
        names = {'config', 'bootstrap', 'bootstrap_cache.save', 'chroot_apt', 'chroot_debianchroot',
                 'chroot_dpkg', 'chroot_hostname', 'chroot_hosts', 'chroot_resolv', 'chroot_sysv-rc'}
        flags = stages['entries']
        require(stages.get('truncated') is False and stages.get('count') == len(names) == len(flags)
                and {item['path'] for item in flags} == {str(BUILD / '.build' / name) for name in names}
                and all(regular(item) and item['bytes'] == 0 for item in flags),
                'Temporary preparation is not the exact approved incomplete lifecycle')
        diversions = report['target_dpkg_diversions']
        require(regular(diversions) and diversions.get('parse_complete') is True
                and diversions.get('raw_utf8_valid') is True and diversions.get('triples_truncated') is False,
                'Diversion metadata is incomplete or unsafe')
        related = [item for item in diversions['triples'] if item['path'] in ('/etc/os-release', '/etc/os-release.debootstrap')
                   or item['diverted_to'] in ('/etc/os-release', '/etc/os-release.debootstrap')]
        require(related == [{'path': '/etc/os-release', 'diverted_to': '/etc/os-release.debootstrap', 'package': ':'}],
                'The exact unambiguous local os-release diversion is absent')
        files = report['target_os_release_files']
        require(len(files) == 3 and all(isinstance(item, dict) for item in files), 'Incomplete os-release inventory')
        paths = {item['image_path']: item for item in files}
        require(set(paths) == {'/etc/os-release', '/etc/os-release.debootstrap', '/usr/lib/os-release'}, 'Unexpected os-release paths')
        backup = paths['/etc/os-release.debootstrap']
        require(backup.get('resolution') == 'absent' and backup['lstat'].get('exists') is False,
                'Backup is not genuinely absent')
        for name in ('/etc/os-release', '/usr/lib/os-release'):
            item = paths[name]
            require(regular(item['lstat']) and regular(item['resolved_lstat']) and item.get('link_steps') == []
                    and item.get('resolution') == 'image-contained-regular' and item.get('resolved_image_path') == name,
                    'Expected regular root-owned non-aliased os-release files')
        vendor = paths['/usr/lib/os-release']; current = paths['/etc/os-release']
        data = vendor['content_utf8'].encode('utf-8'); actual = current['content_utf8'].encode('utf-8')
        require(len(data) == vendor.get('content_bytes') == 286
                and hashlib.sha256(data).hexdigest() == vendor.get('sha256') == 'e249e69c32d81350fdd6b05ac5575255f14e380ba14b8454acea14e49f088bfa'
                and hashlib.md5(data, usedforsecurity=False).hexdigest() == vendor.get('md5') == '776b0aac9b17d49a0ac879da9801f51b',
                'Vendor os-release does not match authenticated base-files bytes')
        expected = report['base_files_os_release_md5sums']
        require(regular(expected) and expected.get('malformed_line_count') == 0
                and [(item['path'], item['expected_md5']) for item in expected['matches']] == [('usr/lib/os-release', vendor['md5'])],
                'Stored base-files os-release MD5 entry differs')
        prefix = data + b'IMAGE_ID=live\nBUILD_ID='
        require(actual.startswith(prefix), 'Image os-release prefix differs from the source algorithm')
        suffix = actual[len(prefix):]
        require(re.fullmatch(rb'[0-9]{8}T[0-9]{6}Z\n', suffix) is not None,
                'Image build timestamp/extra bytes differ from the source algorithm')
        stamp = suffix[:-1].decode('ascii')
        require(datetime.datetime.strptime(stamp, '%Y%m%dT%H%M%SZ').strftime('%Y%m%dT%H%M%SZ') == stamp,
                'Image build timestamp is not a valid UTC calendar value')
        require(current.get('content_bytes') == len(actual) == len(prefix) + 17
                and current.get('sha256') == hashlib.sha256(actual).hexdigest(), 'Current identity metadata differs')
        result.update(accepted=True, reason='Exact source-proven temporary no-rename diversion and authenticated derived identity',
                      build_id=stamp, vendor_sha256=vendor['sha256'], derived_sha256=current['sha256'],
                      derived_bytes=len(actual), diversion=related[0])
        payload['available_md5_no_unexplained_differences'] = True
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        result['reason'] = str(error)


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
    report['target_dpkg_diversions'] = attempt(report, 'target diversions', diversion_inventory)
    report['target_os_release_files'] = [attempt(report, literal, lambda literal=literal: image_os_release(literal))
                                       for literal in ('/etc/os-release', '/etc/os-release.debootstrap', '/usr/lib/os-release')]
    report['base_files_os_release_md5sums'] = attempt(report, 'base-files os-release expected checksum', base_files_os_release_md5sums)
    report['target_apt_archives'] = attempt(report, 'target apt archives', lambda: entries(BUILD / 'chroot/var/cache/apt/archives', 256))
    report['target_apt_partial'] = attempt(report, 'target apt partial', lambda: entries(BUILD / 'chroot/var/cache/apt/archives/partial', 128))
    report['bootstrap_package_cache'] = attempt(report, 'bootstrap packages', lambda: entries(BUILD / 'cache/packages.bootstrap', 128))
    report['target_apt_lists'] = attempt(report, 'target apt lists', lambda: entries(BUILD / 'chroot/var/lib/apt/lists', 128))
    report['target_apt_cache_directory'] = attempt(report, 'target apt cache directory', lambda: entries(BUILD / 'chroot/var/cache/apt', 128))
    reported_indexes = ('deb.debian.org_debian_dists_trixie_main_i18n_Translation-en',
                        'security.debian.org_dists_trixie-security_contrib_binary-amd64_Packages')
    report['reported_apt_indexes'] = []
    for name in reported_indexes:
        path = BUILD / 'chroot/var/lib/apt/lists' / name
        report['reported_apt_indexes'].append(attempt(report, str(path), lambda path=path: apt_index(path)))
    report['target_apt_binary_caches'] = []
    for name in ('pkgcache.bin', 'srcpkgcache.bin'):
        path = BUILD / 'chroot/var/cache/apt' / name
        report['target_apt_binary_caches'].append(attempt(report, str(path), lambda path=path: observe(path)))
    report['source_functions'] = []
    paths = [Path('/usr/share/live/build/functions') / name for name in ('lockfile.sh', 'exit.sh', 'cache.sh', 'stagefile.sh', 'configuration.sh')]
    paths += [Path('/usr/lib/live/build') / name for name in ('build', 'bootstrap', 'bootstrap_cache', 'chroot', 'chroot_prep', 'chroot_cache', 'chroot_tmpfs', 'bootstrap_debootstrap', 'chroot_hacks')]
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
    def payload_verification():
        # Use the builder's verifier, never a target executable or maintainer script.
        info = no_alias(BUILD / 'chroot/var/lib/dpkg/info')
        digest = hashlib.sha256()
        count = total = 0
        for path in sorted(info.glob('*.md5sums')):
            data = read_regular(path, 2 * 1024 * 1024)
            digest.update(path.name.encode() + b'\0' + data + b'\0')
            count += 1
            total += len(data)
            if total > 16 * 1024 * 1024:
                raise ValueError('Stored checksum metadata exceeds bound')
        command = ['/usr/bin/dpkg', '--root=' + str(BUILD / 'chroot'), '--verify-format=rpm', '--verify']
        value = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, timeout=120, check=False)
        stdout, stderr = value.stdout, value.stderr
        truncated = len(stdout) > 32768 or len(stderr) > 8192
        return {'command': command, 'returncode': value.returncode,
                'stdout': stdout[:32768], 'stderr': stderr[:8192], 'output_truncated': truncated,
                'stored_md5_file_count': count, 'stored_md5_metadata_bytes': total,
                'stored_md5_metadata_sha256': digest.hexdigest(),
                'available_md5_no_reported_differences': (value.returncode == 0 and not stdout.strip()
                                                        and not stderr.strip() and not truncated and count > 0),
                'coverage': 'Only available stored MD5 comparisons; not security/all-file verification. Local diversions can omit backup digests; inspect separately.'}
    report['target_payload_verification'] = attempt(report, 'read-only target dpkg verification', payload_verification)
    report['active_build_package_processes'] = attempt(report, 'process scan', processes)
    def numeric_mounts():
        text = read_regular(Path('/proc') / str(os.getpid()) / 'mountinfo', 1024 * 1024).decode(errors='replace')
        return [line[:1024] for line in text.splitlines() if len(line.split()) > 4 and
                line.split()[4].startswith(str(BUILD))][:128]
    report['build_mounts'] = attempt(report, 'mountinfo', numeric_mounts)
    classify_payload(report)
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
