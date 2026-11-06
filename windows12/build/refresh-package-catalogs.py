#!/usr/bin/env python3
"""Guest-only native APT catalog regeneration; never install or invoke live-build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import time

BUILD = Path('/root/windows12-build')
ROOT = BUILD / 'chroot'
OUT = Path('/project-output')
LISTS = ROOT / 'var/lib/apt/lists'
CACHE = ROOT / 'var/cache/apt'
STATUS = 'cf0bdc5bd7e2c0332cb2906f099c044077321f6583fc4eb45eac7d452b2c91e8'
MD5 = '1dfcd7999383a91e54e9cec6729910adcabde8b22f102c81294a239bcfc8bb76'
KEYRING = Path('/usr/share/keyrings/debian-archive-keyring.pgp')
BOUND = 512 * 1024 * 1024
FLAGS = {'config', 'bootstrap', 'bootstrap_cache.save', 'chroot_apt', 'chroot_debianchroot',
         'chroot_dpkg', 'chroot_hostname', 'chroot_hosts', 'chroot_resolv', 'chroot_sysv-rc',
         'chroot_archives', 'chroot_firmware', 'chroot_includes_before_packages',
         'chroot_linux-image', 'chroot_package-lists.install', 'chroot_preseed',
         'chroot_devpts', 'chroot_proc', 'chroot_sysfs'}
CONFIG = {
    'common': '441614d494379408f1eae97f4aafacc67759dc774487250ac90d1a34c8fc45d6',
    'bootstrap': 'a4bce96a1a100177de14a56ce567484b1583f01315e5d1cc4a34fc4a1cc64397',
    'chroot': 'cb6e2dd1c4fd0d08812e4925124a523594981afbc78fb329841f254c95b3ccc1',
    'binary': 'b16bcd609986cf369283406e68ab4e550acf7689788edb36e258bf7dc20b0a55',
    'source': 'b26d96ae9450d13e2df09e7729ee36c9d3f431b7c7c64d2066e6a13b8f2f0ff4'}
REMOTE = {('deb.debian.org', '/debian', 'trixie'), ('deb.debian.org', '/debian', 'trixie-updates'),
          ('security.debian.org', '', 'trixie-security')}
COMPONENTS = {'main', 'contrib', 'non-free', 'non-free-firmware'}


def canonical(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Noncanonical path')
    for p in (path, *path.parents):
        if p.is_symlink():
            raise ValueError('Alias refused: ' + str(p))
    return path


def regular(path, maximum=2 * 1024 * 1024):
    path = canonical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_uid != 0 or before.st_nlink != 1 or before.st_size > maximum:
            raise ValueError('Unsafe/oversized regular file: ' + str(path))
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
        if len(data) > maximum or signature(before) != signature(after):
            raise ValueError('Input changed during read')
    return data


def signature(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode, s.st_uid, s.st_gid, s.st_nlink)


def file_record(path, maximum=256 * 1024 * 1024):
    path = canonical(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        s = os.fstat(stream.fileno())
        local_name = 'windows12-desktop_0.1.0~preview2_all.deb'
        local_pair = {BUILD / 'config/packages.chroot' / local_name, ROOT / 'packages' / local_name}
        linked_local = path in local_pair and s.st_nlink == 2
        if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or (s.st_nlink != 1 and not linked_local) or s.st_size > maximum:
            raise ValueError('Unsafe hash input: ' + str(path) + ' uid=' + str(s.st_uid) + ' links=' + str(s.st_nlink) + ' bytes=' + str(s.st_size))
        if linked_local:
            peer = next(p for p in local_pair if p != path)
            other = canonical(peer).lstat()
            if signature(other) != signature(s) or s.st_size != 7118 or s.st_gid != 0:
                raise ValueError('Unexpected local package hardlink pair')
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise ValueError('Hash input grew past bound')
            digest.update(chunk)
        if signature(s) != signature(os.fstat(stream.fileno())) or total != s.st_size:
            raise ValueError('Hash input changed')
    if linked_local and digest.hexdigest() != '5db8cb011056994620abdfe550a31cbebc492e5a66ce2006551861484adf1776':
        raise ValueError('Linked local package differs from measured deterministic build')
    return {'bytes': total, 'sha256': digest.hexdigest(), 'mode': stat.S_IMODE(s.st_mode),
            'uid': s.st_uid, 'gid': s.st_gid, 'links': s.st_nlink,
            'device': s.st_dev, 'inode': s.st_ino, 'mtime_ns': s.st_mtime_ns}


def tree(path, allow_hook_links=False):
    canonical(path)
    if not path.exists():
        return {'exists': False}
    result, count, total = {}, 0, 0
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(directory) / name
            relative = p.relative_to(path).as_posix()
            count += 1
            if count > 8192 or len(Path(relative).parts) > 16:
                raise ValueError('Tree traversal exceeds bound')
            s = p.lstat()
            if stat.S_ISLNK(s.st_mode):
                dest = os.readlink(p)
                if not (allow_hook_links and p.is_relative_to(BUILD / 'config/hooks')
                        and dest.startswith('/usr/share/live/build/hooks/') and '..' not in Path(dest).parts):
                    raise ValueError('Tree alias refused: ' + str(p))
                result[relative] = {'symlink': dest, 'target': file_record(Path(dest), 1024 * 1024)}
            elif stat.S_ISDIR(s.st_mode):
                result[relative] = {'directory': True, 'mode': stat.S_IMODE(s.st_mode), 'uid': s.st_uid, 'gid': s.st_gid}
            elif stat.S_ISREG(s.st_mode):
                result[relative] = file_record(p)
                total += result[relative]['bytes']
                if total > BOUND:
                    raise ValueError('Tree exceeds 512MiB')
            else:
                raise ValueError('Unsupported tree entry: ' + str(p))
    return {'exists': True, 'entries': result, 'file_bytes': total}


def quiescent():
    uptime = float(Path('/proc/uptime').read_text().split()[0])
    if not 0 < uptime < 1800:
        raise ValueError('Fresh boot under 1800 seconds required')
    mounts = Path('/proc/self/mountinfo').read_text().splitlines()
    if any(len(line.split()) > 4 and (line.split()[4] == str(BUILD) or line.split()[4].startswith(str(BUILD) + '/')) for line in mounts):
        raise ValueError('Target/build mount present')
    names = {'lb', 'live-build', 'apt', 'apt-get', 'aptitude', 'dpkg', 'dpkg-deb', 'debootstrap'}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            raw = (p / 'cmdline').read_bytes()
        except FileNotFoundError:
            continue
        except OSError:
            raise ValueError('Unknown process state')
        if len(raw) > 65536:
            raise ValueError('Process command exceeds bound')
        args = [x.decode(errors='replace') for x in raw.split(b'\0') if x]
        if any(Path(x).name in names or x.startswith('/usr/lib/live/build/') for x in args):
            raise ValueError('Active build/package process')
    return {'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(), 'uptime': uptime}



def bootstrap_inventory():
    # This inactive rootfs cache is never restored or written by metadata update.
    # Preserve its identity/top-level entries without following merged-usr links,
    # opening device nodes or claiming a deep-content checksum.
    root = canonical(BUILD / 'cache/bootstrap')
    names = sorted(root.iterdir())
    if len(names) > 512:
        raise ValueError('Bootstrap top-level inventory exceeds bound')
    def item(path):
        info = path.lstat()
        value = {'mode': info.st_mode, 'uid': info.st_uid, 'gid': info.st_gid,
                 'device': info.st_dev, 'inode': info.st_ino, 'bytes': info.st_size,
                 'mtime_ns': info.st_mtime_ns, 'links': info.st_nlink, 'rdev': info.st_rdev}
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(path)
            if len(target) > 4096:
                raise ValueError('Bootstrap link literal exceeds bound')
            value['link_literal'] = target
        return value
    return {'root': item(root), 'entries': {p.name: item(p) for p in names},
            'coverage': 'Top-level lstat and link literals only; no traversal, device reads or deep content hash.'}


def retained():
    result = {str(p): tree(p, p == BUILD / 'config') for p in
              (BUILD / 'config', BUILD / '.build', ROOT / 'etc/apt', ROOT / 'var/lib/dpkg',
               CACHE / 'archives')}
    result[str(BUILD / 'cache/bootstrap')] = bootstrap_inventory()
    for p in (ROOT / 'var/lib/apt/extended_states', BUILD / '.lock', ROOT / 'root/packages.chroot'):
        result[str(p)] = file_record(p) if canonical(p).exists() else {'exists': False}
    stages = result[str(BUILD / '.build')].get('entries', {})
    if set(stages) != FLAGS or any(item.get('bytes') != 0 or item.get('mode') != 0o644 for item in stages.values()):
        raise ValueError('Exact approved nineteen completed/preparation flags required')
    if result[str(ROOT / 'var/lib/dpkg')]['entries']['status']['sha256'] != STATUS:
        raise ValueError('Unapproved target status')
    h = hashlib.sha256(); count = total = 0
    for p in sorted((ROOT / 'var/lib/dpkg/info').glob('*.md5sums')):
        raw = regular(p); h.update(p.name.encode() + b'\0' + raw + b'\0'); count += 1; total += len(raw)
        if total > 16 * 1024 * 1024:
            raise ValueError('MD5 metadata exceeds bound')
    if (count, total, h.hexdigest()) != (144, 450161, MD5):
        raise ValueError('Unapproved checksum metadata')
    for name, digest in CONFIG.items():
        if result[str(BUILD / 'config')]['entries'][name]['sha256'] != digest:
            raise ValueError('Unapproved saved config')
    return result


def sources():
    from urllib.parse import urlsplit
    paths = [ROOT / 'etc/apt/sources.list']
    parts = ROOT / 'etc/apt/sources.list.d'
    if parts.exists():
        paths += sorted(parts.iterdir())
    found, local, records = set(), 0, []
    for p in paths:
        if not canonical(p).exists():
            continue
        raw = regular(p, 256 * 1024).decode('utf-8')
        records.append({'path': str(p), 'sha256': hashlib.sha256(raw.encode()).hexdigest()})
        if p.suffix not in ('.list', '.sources'):
            raise ValueError('Unknown source directory file')
        if p.suffix == '.sources':
            raise ValueError('Deb822 sources require additional explicit review')
        for line in raw.splitlines():
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            match = re.fullmatch(r'(deb|deb-src)\s+(?:\[([^\]]+)\]\s+)?(\S+)\s+(\S+)(?:\s+(.*))?', line)
            if not match:
                raise ValueError('Unsupported source syntax')
            kind, opts, url, suite, components = match.groups()
            opts = opts.strip() if opts else None
            if opts and opts.strip() not in ('trusted=yes', 'arch=amd64'):
                raise ValueError('Unreviewed source options')
            u = urlsplit(url)
            if u.scheme == 'file':
                if kind != 'deb' or url not in ('file:/packages', 'file:///packages') or suite != './' or components or opts != 'trusted=yes':
                    raise ValueError('Unexpected local source')
                local += 1
                continue
            if opts == 'trusted=yes' or u.scheme not in ('http', 'https') or u.username or u.password or u.port or u.query or u.fragment:
                raise ValueError('Unsafe remote source')
            key = (u.hostname, u.path.rstrip('/'), suite)
            if key not in REMOTE or set((components or '').split()) != COMPONENTS:
                raise ValueError('Unknown remote/suite/components')
            if kind == 'deb':
                found.add(key)
    if found != REMOTE or local != 1:
        raise ValueError('Exact three remote suites and one local source required')
    return records


def fsync_dir(path):
    fd = os.open(canonical(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def exclusive(path, raw, mode=0o600):
    fd = os.open(canonical(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    fsync_dir(path.parent)


def report_write(report, workspace):
    raw = (json.dumps(report, indent=2) + '\n').encode()
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError('Report exceeds bound')
    temp = workspace / ('report-' + str(time.time_ns()) + '.json')
    exclusive(temp, raw)
    os.replace(temp, canonical(OUT / 'package-catalog-refresh.json'))
    fsync_dir(OUT)


def main():
    if os.geteuid() != 0 or not canonical(Path('/run/windows12-build-vm')).is_file():
        raise SystemExit('Contained root builder required')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nonce', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{32}', args.nonce):
        parser.error('Nonce must be32 lowercase hex')
    if Path.cwd() != BUILD:
        raise SystemExit('Fixed build directory required')
    workspace = canonical(OUT / ('catalog-refresh-' + args.nonce))
    workspace.mkdir(mode=0o700)
    report = {'schema': 1, 'nonce': args.nonce, 'refresh_completed': False,
              'outcome': 'preflight', 'quarantined': [], 'started': time.time(),
              'coverage': 'Native APT update only; exporter must independently SQV-verify all signed catalog bytes.'}
    report_write(report, workspace)
    try:
        report['boot'] = quiescent()
        before = retained(); report['before'] = before
        report['target_sources'] = sources()
        report['keyring'] = file_record(KEYRING, 8 * 1024 * 1024)
        report['builder_apt_get'] = file_record(Path('/usr/bin/apt-get'), 16 * 1024 * 1024)
        old = tree(LISTS); report['old_lists'] = old
        local = {name: item for name, item in old['entries'].items() if re.fullmatch(r'_packages_\._(Packages|Release)', name)}
        if set(local) != {'_packages_._Packages', '_packages_._Release'}:
            raise ValueError('Exact retained local Packages/Release pair required')
        binary = {}
        for name in ('pkgcache.bin', 'srcpkgcache.bin'):
            p = CACHE / name
            binary[name] = file_record(p) if canonical(p).exists() else {'exists': False}
        if old['file_bytes'] + sum(item.get('bytes', 0) for item in binary.values()) > BOUND:
            raise ValueError('Combined reproducible catalog caches exceed 512MiB')
        report['old_binary_caches'] = binary
        report_write(report, workspace)
        quarantine = canonical(OUT / ('catalog-quarantine-' + args.nonce))
        quarantine.mkdir(mode=0o700)
        if quarantine.stat().st_dev != LISTS.stat().st_dev:
            raise ValueError('Same filesystem quarantine required')
        if retained() != before or sources() != report['target_sources'] or tree(LISTS) != old:
            raise ValueError('Retained state changed before quarantine')
        quiescent()
        LISTS.rename(quarantine / 'lists'); fsync_dir(LISTS.parent); fsync_dir(quarantine)
        report['quarantined'].append({'source': str(LISTS), 'destination': str(quarantine / 'lists')})
        report_write(report, workspace)
        for name, item in binary.items():
            if item.get('exists') is False:
                continue
            p = CACHE / name
            if file_record(p) != item or p.stat().st_dev != quarantine.stat().st_dev:
                raise ValueError('Binary cache changed or cross-device')
            p.rename(quarantine / name); fsync_dir(CACHE); fsync_dir(quarantine)
            report['quarantined'].append({'source': str(p), 'destination': str(quarantine / name), 'before': item})
            report_write(report, workspace)
        LISTS.mkdir(mode=0o755); fsync_dir(LISTS.parent)
        for name in ('empty-parts', 'archives', 'logs'):
            (workspace / name).mkdir(mode=0o700)
        source_text = ''.join('deb [arch=amd64 signed-by=' + str(KEYRING) + '] https://' + host + path + ' ' + suite + ' main contrib non-free non-free-firmware\n'
                              for host, path, suite in sorted(REMOTE))
        exclusive(workspace / 'sources.list', source_text.encode())
        options = {
            'Dir': '/', 'Dir::Etc': str(workspace), 'Dir::Etc::parts': str(workspace / 'empty-parts'),
            'Dir::Etc::main': str(workspace / 'nonexistent-main'), 'Dir::Etc::sourcelist': str(workspace / 'sources.list'),
            'Dir::Etc::sourceparts': str(workspace / 'empty-parts'), 'Dir::Etc::trusted': str(KEYRING),
            'Dir::Etc::trustedparts': str(workspace / 'empty-parts'),
            'Dir::State': str(ROOT / 'var/lib/apt'), 'Dir::State::status': str(ROOT / 'var/lib/dpkg/status'),
            'Dir::State::lists': str(LISTS), 'Dir::State::extended_states': str(workspace / 'extended_states'),
            'Dir::Cache': str(workspace), 'Dir::Cache::archives': str(workspace / 'archives'),
            'Dir::Cache::pkgcache': '', 'Dir::Cache::srcpkgcache': '', 'Dir::Log': str(workspace / 'logs'),
            'Dir::Bin::methods': '/usr/lib/apt/methods', 'APT::Architecture': 'amd64',
            'Acquire::Languages': 'none', 'Acquire::GzipIndexes': 'false',
            'Acquire::IndexTargets::deb::Packages::KeepCompressed': 'false',
            'Acquire::IndexTargets::deb::DEP-11::DefaultEnabled': 'false',
            'Acquire::Retries': '2', 'Acquire::http::Timeout': '45', 'Acquire::https::Timeout': '45',
            'Acquire::AllowInsecureRepositories': 'false', 'Acquire::AllowDowngradeToInsecureRepositories': 'false',
            'Acquire::https::Verify-Peer': 'true', 'Acquire::https::Verify-Host': 'true',
            'APT::Get::AllowUnauthenticated': 'false', 'APT::Update::Error-Mode': 'any',
            'APT::Sandbox::User': 'root'}
        for scheme in ('http', 'https'):
            proxy = os.environ.get(scheme + '_proxy') or os.environ.get(scheme.upper() + '_PROXY')
            if proxy:
                options['Acquire::' + scheme + '::Proxy'] = proxy
        ca = os.environ.get('SSL_CERT_FILE')
        if ca:
            file_record(Path(ca), 8 * 1024 * 1024)
            options['Acquire::https::CaInfo'] = ca
        config = ''.join(key + ' ' + json.dumps(value) + ';\n' for key, value in options.items())
        config += ''.join('#clear ' + key + ';\n' for key in (
            'APT::Update::Pre-Invoke', 'APT::Update::Post-Invoke', 'APT::Update::Post-Invoke-Success',
            'DPkg::Pre-Invoke', 'DPkg::Post-Invoke', 'DPkg::Pre-Install-Pkgs',
            'APT::Install::Pre-Invoke', 'APT::Install::Post-Invoke'))
        exclusive(workspace / 'apt.conf', config.encode())
        env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'HOME': str(workspace), 'TMPDIR': str(workspace),
               'XDG_CACHE_HOME': str(workspace), 'XDG_CONFIG_HOME': str(workspace), 'XDG_DATA_HOME': str(workspace),
               'XDG_STATE_HOME': str(workspace), 'LC_ALL': 'C', 'APT_CONFIG': str(workspace / 'apt.conf')}
        command = ['/usr/bin/apt-get', 'update']
        report['command'] = command
        report['private_config_sha256'] = hashlib.sha256(config.encode()).hexdigest()
        report['outcome'] = 'updating'; report_write(report, workspace)
        def limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024 * 1024, 256 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
        with (workspace / 'update.out').open('xb') as stdout, (workspace / 'update.err').open('xb') as stderr:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     cwd=workspace, env=env, start_new_session=True, preexec_fn=limits)
            deadline = time.monotonic() + 600
            while child.poll() is None:
                if time.monotonic() >= deadline or stdout.tell() > 4 * 1024 * 1024 or stderr.tell() > 4 * 1024 * 1024:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
                    raise ValueError('Native update exceeded timeout/output bound')
                time.sleep(0.2)
            report['update_returncode'] = child.returncode
        report['update_output'] = {name: file_record(workspace / name, 8 * 1024 * 1024) for name in ('update.out', 'update.err')}
        if child.returncode:
            raise ValueError('Native update failed; partial catalogs retained')
        for name, expected in local.items():
            old_path = quarantine / 'lists' / name
            if file_record(old_path) != expected:
                raise ValueError('Retained local catalog changed')
            exclusive(LISTS / name, regular(old_path, 64 * 1024 * 1024), expected['mode'])
        after = retained(); report['after'] = after
        if after != before or sources() != report['target_sources']:
            raise ValueError('Preserved target state changed')
        if tree(quarantine / 'lists') != old:
            raise ValueError('Quarantined catalog evidence changed')
        for name, item in binary.items():
            if item.get('exists') is not False and file_record(quarantine / name) != item:
                raise ValueError('Quarantined binary cache evidence changed')
            if canonical(CACHE / name).exists():
                raise ValueError('Target binary cache unexpectedly recreated')
        if file_record(KEYRING, 8 * 1024 * 1024) != report['keyring'] or file_record(Path('/usr/bin/apt-get'), 16 * 1024 * 1024) != report['builder_apt_get']:
            raise ValueError('Builder APT/keyring changed during update')
        if regular(workspace / 'apt.conf') != config.encode() or regular(workspace / 'sources.list') != source_text.encode():
            raise ValueError('Private APT configuration changed during update')
        report['new_lists'] = tree(LISTS)
        report['retained_local_catalogs'] = {name: file_record(LISTS / name) for name in local}
        report['quarantine'] = str(quarantine)
        report['boot_after'] = quiescent()
        if report['boot_after']['boot_id'] != report['boot']['boot_id']:
            raise ValueError('Boot identity changed')
        report.update(refresh_completed=True, outcome='native-update-complete-independent-catalog-audit-required')
        return 0
    except (OSError, ValueError, KeyError, UnicodeError, subprocess.SubprocessError) as error:
        report.update(outcome='failed-partial-and-quarantine-preserved', error=str(error)[:2000])
        return 1
    finally:
        if not report['refresh_completed']:
            for label, action in (('retained_after_failure', retained), ('lists_after_failure', lambda: tree(LISTS))):
                try:
                    report[label] = action()
                except (OSError, ValueError, KeyError) as error:
                    report[label + '_error'] = str(error)[:1000]
        report['finished'] = time.time(); report_write(report, workspace)


if __name__ == '__main__':
    raise SystemExit(main())
