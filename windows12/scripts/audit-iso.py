#!/usr/bin/env python3
"""Audit a real contained ISO against its checksum and frozen source snapshot.
No mounts, guest-root extraction, package installation or image code execution.
Content audit success does not establish bootability or installation support.
"""
import argparse
import ast
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import select
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / '.work/builder/iso-tools'
PREFIX = '__W12_AUDIT_ROOT__'
CORE_PACKAGES = (
    'plasma-desktop', 'plasma-workspace', 'sddm', 'dolphin', 'plasma-discover',
    'calamares', 'calamares-settings-debian', 'chromium', 'firefox-esr',
    'libreoffice-writer', 'libreoffice-calc', 'libreoffice-impress',
    'network-manager', 'plasma-nm', 'python3', 'xdg-utils', 'linux-image-amd64',
)


def contained(path):
    path = Path(os.path.abspath(path))
    if path == ROOT or not path.resolve().is_relative_to(ROOT):
        raise ValueError('Path must stay beneath project: ' + str(path))
    for component in [path, *path.parents]:
        if component == ROOT:
            break
        if component.is_symlink():
            raise ValueError('Symlink path refused: ' + str(component))
    return path


def regular(path):
    path = contained(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Regular input file required: ' + str(path))
    return path


def sha256(path):
    digest = hashlib.sha256()
    with regular(path).open('rb') as source:
        for block in iter(lambda: source.read(2 ** 20), b''):
            digest.update(block)
    return digest.hexdigest()


def snapshot(path):
    value = regular(path).stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def environment(output, tools=True):
    env = os.environ.copy()
    for variable, leaf in {'HOME': 'home', 'TMPDIR': 'tmp', 'XDG_CACHE_HOME': 'cache',
                           'XDG_CONFIG_HOME': 'config', 'XDG_DATA_HOME': 'data',
                           'XDG_STATE_HOME': 'state', 'XDG_RUNTIME_DIR': 'runtime'}.items():
        directory = contained(output / leaf)
        directory.mkdir(mode=0o700, exist_ok=True)
        env[variable] = str(directory)
    env.update(PYTHONDONTWRITEBYTECODE='1', LC_ALL='C', TZ='UTC')
    env.pop('LD_PRELOAD', None)
    env.pop('LD_LIBRARY_PATH', None)
    env.pop('QEMU_MODULE_DIR', None)
    if tools:
        env['LD_LIBRARY_PATH'] = f'{TOOLS}/usr/lib/x86_64-linux-gnu:{TOOLS}/lib/x86_64-linux-gnu'
    return env


class Commands:
    def __init__(self, output):
        self.output = output
        self.env = environment(output)
        self.count = 0

    def run(self, arguments, *, limit=64 * 2 ** 20, timeout=300, host=False):
        self.count += 1
        stderr = self.output / f'command-{self.count:03d}.stderr'
        record = {'number': self.count, 'arguments': [str(a) for a in arguments], 'started_unix': time.time()}
        with (self.output / 'commands.jsonl').open('a') as log:
            log.write(json.dumps(record) + '\n')
        with stderr.open('xb') as errors:
            process = subprocess.Popen([str(a) for a in arguments], env=environment(self.output, False) if host else self.env,
                                       cwd=self.output, stdout=subprocess.PIPE, stderr=errors)
            data = bytearray()
            deadline = time.monotonic() + timeout
            try:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(arguments, timeout)
                    if not select.select([process.stdout], [], [], min(1, remaining))[0]:
                        continue
                    block = os.read(process.stdout.fileno(), 65536)
                    if not block:
                        break
                    if len(data) + len(block) > limit:
                        raise ValueError('Tool output exceeded audit bound: ' + str(arguments[0]))
                    data.extend(block)
                process.wait(timeout=max(0.01, deadline - time.monotonic()))
                if process.returncode:
                    raise subprocess.CalledProcessError(process.returncode, arguments)
                return bytes(data)
            finally:
                process.stdout.close()
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


def verify_tool(package, relative_binary, commands, lock):
    entry = lock.get(package)
    if not isinstance(entry, dict) or not re.fullmatch(r'[0-9a-f]{64}', entry.get('SHA256', '')):
        raise ValueError('Authenticated package lock missing: ' + package)
    binary = regular(TOOLS / relative_binary)
    archive = regular(ROOT / '.work/builder/debs' / Path(entry['Filename']).name)
    if sha256(archive) != entry['SHA256']:
        raise ValueError('Cached package SHA256 mismatch: ' + package)
    decompressor = shutil.which('dpkg-deb')
    if not decompressor:
        raise ValueError('Read-only dpkg-deb utility required; no host installation attempted')
    payload = commands.run([decompressor, '--fsys-tarfile', archive], host=True, limit=128 * 2 ** 20)
    matches = []
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive_tar:
        for member in archive_tar:
            if member.name.removeprefix('./') == relative_binary:
                if not member.isfile() or member.size > 32 * 2 ** 20:
                    raise ValueError('Unexpected executable member in package: ' + package)
                matches.append(hashlib.sha256(archive_tar.extractfile(member).read()).hexdigest())
    actual = sha256(binary)
    if matches != [actual]:
        raise ValueError('Extracted executable differs from authenticated package: ' + package)
    return binary, {'package': entry.get('Package'), 'version': entry.get('Version'),
                    'deb_sha256': entry['SHA256'], 'binary_sha256': actual}


def check_checksum(iso, actual, explicit, checksum_file):
    evidence = {}
    if explicit:
        if not re.fullmatch(r'[0-9a-f]{64}', explicit) or explicit != actual:
            raise ValueError('Explicit ISO SHA256 mismatch/invalid digest')
        evidence['supplied_sha256'] = explicit
    selected = checksum_file
    if selected is None and (iso.parent / 'SHA256SUMS').exists():
        selected = iso.parent / 'SHA256SUMS'
    if selected is not None:
        selected = regular(selected)
        matches = []
        for line in selected.read_text().splitlines():
            match = re.fullmatch(r'([0-9a-f]{64}) ([ *])(.+)', line)
            if not match:
                raise ValueError('Malformed SHA256SUMS line')
            if match[3] == iso.name:
                matches.append(match[1])
        if matches != [actual]:
            raise ValueError('SHA256SUMS must contain exactly one matching ISO digest/name')
        evidence.update(checksum_file=str(selected), checksum_file_sha256=sha256(selected))
    if not evidence:
        raise ValueError('Supply --sha256/--checksum-file, or retain adjacent SHA256SUMS')
    return evidence


def frozen_overlay(archive_path, lock_path):
    expected = regular(lock_path).read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{64}', expected) or sha256(archive_path) != expected:
        raise ValueError('Frozen source archive SHA256 differs from source lock')
    if regular(archive_path).stat().st_size > 64 * 2 ** 20:
        raise ValueError('Source archive exceeds audit bound')
    overlay = {}
    packager = None
    seen = set()
    with tarfile.open(archive_path, mode='r:*') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or member.issym() or member.islnk():
                raise ValueError('Unsafe member in frozen source archive')
            name = str(path)
            if name in seen:
                raise ValueError('Duplicate member in frozen source archive: ' + name)
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile() or member.size > 16 * 2 ** 20:
                raise ValueError('Unsupported source archive member: ' + name)
            if name.startswith('image/') or name == 'scripts/package-desktop.py':
                data = archive.extractfile(member).read()
                if name.startswith('image/'):
                    overlay['/' + name.removeprefix('image/')] = data
                else:
                    packager = data.decode('utf-8')
    if not overlay or packager is None or sum(map(len, overlay.values())) > 64 * 2 ** 20:
        raise ValueError('Missing/excessive frozen overlay or packager')
    versions = []
    for node in ast.parse(packager).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                versions.append(node.value.value)
    if len(versions) != 1 or not re.fullmatch(r'[0-9][A-Za-z0-9.+:~\-]*', versions[0]):
        raise ValueError('Expected package version not a single literal in frozen packager')
    for required in ['/usr/local/bin/windows12-webapp', '/usr/local/bin/windows12-welcome',
                     '/usr/local/share/windows12/welcome.html',
                     '/usr/share/wallpapers/Windows12/contents/images/3840x2160.svg']:
        if required not in overlay:
            raise ValueError('Required managed source asset missing: ' + required)
    return overlay, versions[0], expected


def image_path(value):
    parts = []
    for part in value.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            if not parts:
                raise ValueError('Image symlink escapes its root')
            parts.pop()
        else:
            parts.append(part)
    return '/' + '/'.join(parts)


def squash_listing(data):
    entries = {}
    pattern = re.compile(r'^([bcdlps-][rwxStTs-]{9})\s+[0-9]+/[0-9]+\s+([0-9]+(?:,\s*[0-9]+)?)\s+[0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}\s+' + PREFIX + r'(.*)$')
    for line in data.decode('utf-8').splitlines():
        match = pattern.fullmatch(line)
        if not match:
            # Ignore tool headers, but never silently skip a malformed entry.
            if PREFIX in line:
                raise ValueError('Unrecognized SquashFS listing entry: ' + line[:200])
            continue
        suffix = match[3]
        target = None
        if match[1][0] == 'l':
            if ' -> ' not in suffix:
                raise ValueError('Symlink listing lacks target')
            suffix, target = suffix.split(' -> ', 1)
        path = image_path(suffix)
        if path in entries or (suffix and not suffix.startswith('/')):
            raise ValueError('Duplicate/malformed SquashFS entry')
        entries[path] = {'mode': match[1], 'size': int(match[2]) if match[2].isdigit() else 0, 'target': target}
    if '/' not in entries or '/var/lib/dpkg/status' not in entries:
        raise ValueError('Incomplete/unrecognized SquashFS listing')
    return entries


def resolve_image(path, entries):
    path = image_path(path)
    for _ in range(32):
        parts = PurePosixPath(path).parts[1:]
        for index in range(len(parts)):
            prefix = '/' + '/'.join(parts[:index + 1])
            entry = entries.get(prefix)
            if entry is None:
                raise ValueError('Image path missing: ' + prefix)
            if entry['mode'][0] == 'l':
                target = entry['target']
                if not target:
                    raise ValueError('Empty image symlink target')
                replacement = target if target.startswith('/') else str(PurePosixPath(prefix).parent / target)
                path = image_path(replacement + '/' + '/'.join(parts[index + 1:]))
                break
        else:
            return path
    raise ValueError('Excessive/cyclic image symlinks')


def audit(args, iso, output, result):
    commands = Commands(output)
    iso_before = snapshot(iso)
    actual = sha256(iso)
    result.update(iso_sha256=actual, checksum=check_checksum(iso, actual, args.sha256, args.checksum_file))
    source = regular(args.source_archive)
    source_before = snapshot(source)
    source_lock = regular(args.source_lock or source.with_name('build-source.sha256'))
    overlay, version, source_digest = frozen_overlay(source, source_lock)
    result.update(source_archive=str(source), source_sha256=source_digest, expected_package_version=version)
    lock = json.loads(regular(ROOT / 'build/iso-tools-lock.json').read_text())
    xorriso, xorriso_evidence = verify_tool('xorriso', 'usr/bin/xorriso', commands, lock)
    unsquashfs, squash_evidence = verify_tool('squashfs-tools', 'usr/bin/unsquashfs', commands, lock)
    result['tools'] = {'xorriso': xorriso_evidence, 'unsquashfs': squash_evidence}
    listing = commands.run([xorriso, '-indev', iso, '-find', '/', '-type', 'f', '-exec', 'echo', '--'])
    (output / 'iso-tree-files.txt').write_bytes(listing)
    files = set()
    for line in listing.decode('utf-8').splitlines():
        words = shlex.split(line)
        if len(words) == 1 and words[0].startswith('/'):
            if '..' in PurePosixPath(words[0]).parts:
                raise ValueError('Traversal in ISO listing')
            files.add(words[0])
    if '/live/filesystem.squashfs' not in files:
        raise ValueError('Expected regular /live/filesystem.squashfs absent from ISO')
    if not any(p.startswith('/live/vmlinuz') for p in files) or not any(p.startswith('/live/initrd') for p in files):
        raise ValueError('Live kernel/initrd absent from ISO listing')
    report = commands.run([xorriso, '-indev', iso, '-report_el_torito', 'plain'])
    # xorriso versions may put report lines on either output stream.
    report += (output / f'command-{commands.count:03d}.stderr').read_bytes()
    (output / 'el-torito-report.txt').write_bytes(report)
    boots = re.findall(r'^El Torito boot img\s*:\s*([0-9]+)\s+(\S+)\s+(\S+)', report.decode('utf-8'), re.M)
    if not boots or not any(flag.lower() == 'y' for _, _, flag in boots):
        raise ValueError('No enabled El Torito boot-image entry reported; no bootability inferred')
    result['el_torito_entries'] = [{'index': int(i), 'platform': platform, 'bootable_flag': flag} for i, platform, flag in boots]
    squash = contained(output / 'filesystem.squashfs')
    if squash.exists():
        raise ValueError('SquashFS destination already exists')
    if shutil.disk_usage(output).free < iso.stat().st_size + 256 * 2 ** 20:
        raise ValueError('Insufficient free space for bounded ISO payload extraction')
    extraction = commands.run([xorriso, '-osirrox', 'on', '-indev', iso, '-extract', '/live/filesystem.squashfs', squash], timeout=900)
    (output / 'iso-extract.stdout').write_bytes(extraction)
    regular(squash)
    with squash.open('rb') as source_file:
        if source_file.read(4) != b'hsqs':
            raise ValueError('Extracted payload lacks little-endian SquashFS signature')
    result['squashfs_sha256'] = sha256(squash)
    options = [unsquashfs, '-no-progress', '-processors', '2', '-data-queue', '32', '-frag-queue', '32', '-strict-errors']
    information = commands.run(options + ['-stat', squash])
    (output / 'squashfs-superblock.txt').write_bytes(information)
    listing = commands.run(options + ['-lln', '-d', PREFIX, squash], limit=128 * 2 ** 20)
    (output / 'squashfs-listing.txt').write_bytes(listing)
    entries = squash_listing(listing)
    result['squashfs_entries'] = len(entries)
    cache = {}

    def read(path, limit=16 * 2 ** 20):
        resolved = resolve_image(path, entries)
        entry = entries[resolved]
        if entry['mode'][0] != '-' or entry['size'] > limit:
            raise ValueError('Audit target is not a bounded regular image file: ' + path)
        if resolved not in cache:
            data = commands.run(options + ['-cat', '-no-wildcards', squash, resolved.lstrip('/')], limit=limit)
            if len(data) != entry['size']:
                raise ValueError('Image file length mismatch: ' + path)
            cache[resolved] = data
        return cache[resolved]

    status_data = read('/var/lib/dpkg/status', 32 * 2 ** 20)
    records = []
    package_records = {}
    for block in status_data.decode('utf-8').split('\n\n'):
        fields = {}
        for line in block.splitlines():
            if line and not line[0].isspace() and ': ' in line:
                key, value = line.split(': ', 1)
                fields[key] = value
        if fields.get('Package'):
            package_records.setdefault(fields['Package'], []).append(fields)
        if fields.get('Package') == 'windows12-desktop':
            records.append(fields)
    if len(records) != 1 or records[0].get('Status') != 'install ok installed' or records[0].get('Version') != version:
        raise ValueError('Overlay package missing, not installed, ambiguous, or wrong version')
    core_versions = {}
    for package in CORE_PACKAGES:
        candidates = package_records.get(package, [])
        if (len(candidates) != 1 or candidates[0].get('Status') != 'install ok installed'
                or not candidates[0].get('Version')):
            raise ValueError('Required core package missing, ambiguous or not installed: ' + package)
        core_versions[package] = candidates[0]['Version']
    result['installed_core_package_versions'] = core_versions
    owned = set(read('/var/lib/dpkg/info/windows12-desktop.list').decode('utf-8').splitlines())
    os_release = read('/etc/os-release').decode('utf-8')
    if not re.search(r'^ID=(["\']?)debian\1$', os_release, re.M):
        raise ValueError('Expected Debian target identity absent')
    (output / 'target-os-release.txt').write_text(os_release)
    checks = []
    for path, expected_bytes in sorted(overlay.items()):
        if path not in owned:
            raise ValueError('Managed overlay path absent from package file list: ' + path)
        entry = entries.get(path)
        if entry is None or entry['mode'][0] != '-':
            raise ValueError('Managed overlay path is not a regular image file: ' + path)
        mode = entry['mode']
        if mode[8] == 'w':
            raise ValueError('Managed overlay file is world-writable: ' + path)
        if path in ('/usr/local/bin/windows12-webapp', '/usr/local/bin/windows12-welcome'):
            if not all(mode[index] == 'x' for index in (3, 6, 9)) or mode[5] == 'w':
                raise ValueError('Managed launcher lacks expected execute bits or is group-writable: ' + path)
        actual_bytes = read(path)
        if actual_bytes != expected_bytes:
            raise ValueError('Managed file differs from frozen source: ' + path)
        checks.append({'path': path, 'mode': mode, 'sha256': hashlib.sha256(actual_bytes).hexdigest()})
    help_text = read('/usr/local/share/windows12/welcome.html').decode('utf-8').lower()
    if not all(phrase in help_text for phrase in ['independent of microsoft', 'linux', 'partial', 'offline']):
        raise ValueError('Independent Linux/help compatibility wording absent')
    known_ca = {'windows12-build-proxy.crt', 'windows12-build-proxy.pem'}
    for path, entry in entries.items():
        if PurePosixPath(path).name in known_ca or (entry['target'] and PurePosixPath(entry['target']).name in known_ca):
            raise ValueError('Known transient build CA path/link remains: ' + path)
    if '/etc/apt/apt.conf.d/80windows12-build-proxy' in entries:
        raise ValueError('Known transient apt proxy file remains')
    scanned = []
    for path, entry in sorted(entries.items()):
        if not (path.startswith('/etc/apt/') or path == '/etc/environment') or entry['mode'][0] not in ('-', 'l'):
            continue
        # Fail closed on directory aliases rather than silently missing active
        # configuration stored outside the listed /etc/apt subtree.
        resolved = resolve_image(path, entries)
        if entries[resolved]['mode'][0] == 'd':
            raise ValueError('APT directory alias requires explicit audit support: ' + path)
        for line in read(path, 4 * 2 ** 20).decode('utf-8', errors='replace').splitlines():
            if line.strip().startswith(('#', '//')):
                continue
            if 'proxy' in line.lower() and re.search(r'(?<![0-9.])10[.]0[.]2[.]2(?![0-9.])', line):
                raise ValueError('Transient build proxy entry remains: ' + path)
        scanned.append(path)
    if snapshot(iso) != iso_before or snapshot(source) != source_before:
        raise ValueError('ISO/source changed during audit; results invalid')
    result.update(audit_passed=True, outcome='content-audit-passed', managed_files=checks,
                  installed_package={'name': 'windows12-desktop', 'version': version, 'status': 'install ok installed'},
                  independent_linux_help=True, known_build_ca_paths_absent=True,
                  known_build_proxy_entries_absent=True, proxy_files_scanned=scanned)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--source-archive', type=Path, required=True, help='Frozen build checks.tar, never current working tree')
    parser.add_argument('--source-lock', type=Path, help='Plain SHA256 lock; defaults to archive sibling build-source.sha256')
    parser.add_argument('--checksum-file', type=Path, help='GNU SHA256SUMS; otherwise use adjacent file if present')
    parser.add_argument('--sha256', help='Expected lowercase ISO SHA256; adjacent checksum also checked when present')
    parser.add_argument('--output', type=Path, help='NEW contained output directory, never reused')
    args = parser.parse_args()
    iso = regular(args.iso)
    if iso.suffix.lower() != '.iso':
        raise ValueError('A real regular .iso input is required')
    with iso.open('rb') as source:
        source.seek(32769)
        if source.read(5) != b'CD001':
            raise ValueError('Input lacks ISO9660 volume signature')
    regular(args.source_archive)
    output = contained(args.output or ROOT / 'artifacts' / f'iso-audit-{time.time_ns()}')
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; no output reuse/overwrite permitted')
    output.mkdir(parents=True, mode=0o700)
    result = {'iso': str(iso), 'output': str(output), 'audit_passed': False, 'boot_verified': False,
              'install_verified': False, 'gui_verified': False, 'started_unix': time.time(), 'outcome': 'starting'}
    try:
        audit(args, iso, output, result)
        return 0
    except KeyboardInterrupt:
        result['outcome'] = 'interrupted'
        return 130
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError, tarfile.TarError, KeyError, SyntaxError) as error:
        result.update(outcome='failed', error=str(error))
        print(str(error), file=sys.stderr)
        return 1
    finally:
        result['finished_unix'] = time.time()
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('Audit evidence:', output, '; boot/install/GUI remain unverified.')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
