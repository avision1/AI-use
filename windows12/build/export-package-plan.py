#!/usr/bin/env python3
"""Guest-only retained live-build install-pass URI planner. Never downloads/installs."""
import argparse
import datetime
import email.utils
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import time
from urllib.parse import urlsplit, unquote

BUILD = Path('/root/windows12-build')
ROOT = BUILD / 'chroot'
OUT = Path('/project-output')
MAX = 2 * 1024 * 1024


def regular(path, limit=MAX):
    path = Path(path)
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError('Symlink refused: ' + str(parent))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        s = os.fstat(stream.fileno())
        if not stat.S_ISREG(s.st_mode) or s.st_size > limit:
            raise ValueError('Not a bounded regular file: ' + str(path))
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
        if len(data) > limit or (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError('File changed or exceeded limit: ' + str(path))
        return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def evidence(path, limit=MAX):
    data = regular(path, limit)
    return {'path': str(path), 'size': len(data), 'sha256': digest(data)}


def run(argv, workspace, label, limit=MAX, timeout=90, env=None):
    """File-backed bounded output, time and file-size limits; no shell."""
    output, error = workspace / (label + '.out'), workspace / (label + '.err')
    def bounds():
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
    with output.open('xb') as stdout, error.open('xb') as stderr:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=stdout,
                                stderr=stderr, env=env, cwd=workspace,
                                timeout=timeout, check=False, preexec_fn=bounds)
    raw, err = regular(output, limit), regular(error, limit)
    if result.returncode:
        raise ValueError(label + ' failed: ' + err.decode(errors='replace')[:1500])
    return raw


def paragraphs(raw):
    for paragraph in raw.decode('utf-8').split('\n\n'):
        fields, last = {}, None
        for line in paragraph.splitlines():
            if line.startswith((' ', '\t')) and last:
                fields[last] += '\n' + line
            elif ': ' in line:
                last, value = line.split(': ', 1)
                if last in fields:
                    raise ValueError('Duplicate catalog field')
                fields[last] = value
            elif line.endswith(':'):
                last = line[:-1]
                fields[last] = ''
        if fields:
            yield fields


def provenance():
    paths = [ROOT / 'var/lib/dpkg/status', ROOT / 'var/lib/apt/extended_states']
    visited = 0
    for directory in [ROOT / 'etc/apt', BUILD / 'config', BUILD / '.build']:
        if directory.exists():
            for p in directory.rglob('*'):
                visited += 1
                if visited > 4096 or len(p.relative_to(directory).parts) > 16:
                    raise ValueError('Provenance traversal exceeds bounded scope')
                info = p.lstat()
                if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                    raise ValueError('Unsupported provenance path type: ' + str(p))
                if stat.S_ISREG(info.st_mode):
                    paths.append(p)
                    if len(paths) > 512:
                        raise ValueError('Too many provenance files')
    result, total = [], 0
    for p in sorted(set(paths)):
        if p.exists():
            item = evidence(p, 32 * 1024 * 1024)
            total += item['size']
            if total > 64 * 1024 * 1024:
                raise ValueError('Provenance bytes exceed bound')
            result.append(item)
    return result


def catalogs(workspace, env):
    lists = ROOT / 'var/lib/apt/lists'
    keyring = Path('/usr/share/keyrings/debian-archive-keyring.gpg')
    verified, records = [], []
    release_paths = sorted(lists.glob('*_InRelease'))
    if not release_paths or len(release_paths) > 16:
        raise ValueError('Expected bounded retained signed InRelease catalogs')
    matched = set()
    for number, release in enumerate(release_paths):
        regular(release, 8 * 1024 * 1024)
        clear = workspace / ('release-' + str(number))
        run(['/usr/bin/gpgv', '--keyring', str(keyring), '--output', str(clear), str(release)],
            workspace, 'gpgv-' + str(number), env=env)
        fields = list(paragraphs(regular(clear, 8 * 1024 * 1024)))[0]
        now = time.time()
        for field in ('Date', 'Valid-Until'):
            if field in fields:
                stamp = email.utils.parsedate_to_datetime(fields[field]).timestamp()
                if (field == 'Date' and stamp > now + 86400) or (field == 'Valid-Until' and stamp < now):
                    raise ValueError('Signed catalog date invalid: ' + str(release))
        if 'SHA256' not in fields:
            raise ValueError('Signed release lacks SHA256')
        prefix = release.name[:-len('InRelease')]
        covered = []
        for line in fields['SHA256'].splitlines():
            parts = line.split()
            if len(parts) != 3 or not parts[2].endswith('/Packages'):
                continue
            sha, length, relative = parts
            if not re.fullmatch('[0-9a-f]{64}', sha) or not re.fullmatch(r'[A-Za-z0-9+./_-]+', relative) or '..' in relative:
                raise ValueError('Unsafe release index identity')
            name = prefix + relative.replace('/', '_')
            candidates = [p for p in (lists / name, lists / (name + '.lz4'), lists / (name + '.xz'), lists / (name + '.gz')) if p.exists()]
            if not candidates:
                continue
            if len(candidates) != 1 or int(length) > 256 * 1024 * 1024:
                raise ValueError('Ambiguous or oversized package index')
            p = candidates[0]
            item = evidence(p, 256 * 1024 * 1024)
            raw = run(['/usr/lib/apt/apt-helper', 'cat-file', str(p)], workspace,
                      'index-' + str(len(matched)), 256 * 1024 * 1024, env=env)
            if len(raw) != int(length) or digest(raw) != sha:
                raise ValueError('Packages index does not match signed SHA256: ' + str(p))
            for record in paragraphs(raw):
                if all(k in record for k in ('Package', 'Version', 'Filename', 'Size', 'SHA256')):
                    records.append({k: record[k] for k in ('Package', 'Version', 'Filename', 'Size', 'SHA256')})
            item.update(uncompressed_sha256=sha, uncompressed_size=len(raw), release_path=relative)
            covered.append(item)
            matched.add(p.name)
        verified.append({'inrelease': evidence(release, 8 * 1024 * 1024), 'indexes': covered})
    # Local unsigned file repository is explicitly excluded from remote trust.
    unexpected = [p.name for p in lists.iterdir() if '_Packages' in p.name and p.name not in matched and not p.name.startswith('_packages_')]
    if unexpected or not matched:
        raise ValueError('Unverified or absent remote package catalogs: ' + repr(unexpected))
    return records, verified, evidence(keyring)


def main():
    if os.geteuid() != 0 or not Path('/run/windows12-build-vm').is_file():
        raise ValueError('Refusing host execution: root and VM marker required')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nonce', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{32}', args.nonce):
        raise ValueError('Fresh nonce must be 32 lowercase hex characters')
    regular('/run/windows12-build-vm', 4096)
    # Exclusive directory permanently consumes the nonce; never remove prior evidence.
    for parent in (OUT, *OUT.parents):
        if parent.is_symlink():
            raise ValueError('Planning output ancestor alias refused')
    workspace = OUT / ('package-plan-' + args.nonce)
    workspace.mkdir(mode=0o700)
    env = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C', 'HOME': str(workspace),
           'TMPDIR': str(workspace), 'XDG_CACHE_HOME': str(workspace)}
    queue = ROOT / 'root/packages.chroot'
    for name in ('config', 'bootstrap', 'chroot_package-lists.install', 'chroot_linux-image', 'chroot_firmware'):
        regular(BUILD / '.build' / name, 4096)
    if (BUILD / '.build/chroot_install-packages.install').exists():
        raise ValueError('Install pass is already complete')
    installed_source = Path('/usr/lib/live/build/chroot_install-packages')
    if digest(regular(installed_source, 128 * 1024)) != '64e6621e6478ceebc1268e83d1a37a8fc874691d70cab9cdb2be53c899c66f8f':
        raise ValueError('Installed live-build install-pass source differs from reviewed source')
    raw = regular(queue, 128 * 1024)
    packages = raw.decode().split()
    if not packages or len(packages) > 4096 or not all(re.fullmatch(r'[a-z0-9][a-z0-9+.-]*(?::[a-z0-9-]+)?(?:=[A-Za-z0-9.+:~_-]+)?', p) for p in packages):
        raise ValueError('Missing or unsupported exact live-build package queue')
    if (ROOT / 'root/packages.foreign-architectures').exists():
        if regular(ROOT / 'root/packages.foreign-architectures', 4096).strip():
            raise ValueError('Unapplied foreign architectures require separate review')
    before = provenance()
    records, signed, keyring = catalogs(workspace, env)
    by_sha = {}
    for record in records:
        by_sha.setdefault(record['SHA256'], []).append(record)
    # APT_CONFIG is read before config fragments. Final -c clears executable hooks.
    initial = workspace / 'initial.conf'
    final = workspace / 'final.conf'
    initial.write_text('Dir::Etc "' + str(ROOT / 'etc/apt') + '";\n')
    final.write_text('\n'.join('#clear ' + key + ';' for key in (
        'APT::Install::Pre-Invoke', 'APT::Install::Post-Invoke',
        'DPkg::Pre-Invoke', 'DPkg::Post-Invoke', 'DPkg::Pre-Install-Pkgs',
        'APT::Get::Pre-Install-Pkgs', 'APT::Update::Pre-Invoke', 'APT::Update::Post-Invoke')) + '\n')
    env['APT_CONFIG'] = str(initial)
    selections = {'Dir': str(ROOT), 'Dir::State': str(ROOT / 'var/lib/apt'),
                  'Dir::State::status': str(ROOT / 'var/lib/dpkg/status'),
                  'Dir::State::lists': str(ROOT / 'var/lib/apt/lists'),
                  'Dir::State::extended_states': str(ROOT / 'var/lib/apt/extended_states'),
                  'Dir::Cache': str(ROOT / 'var/cache/apt'),
                  'Dir::Cache::archives': str(ROOT / 'var/cache/apt/archives'),
                  'Dir::Cache::pkgcache': '', 'Dir::Cache::srcpkgcache': '',
                  'Dir::Etc': str(ROOT / 'etc/apt'), 'Debug::NoLocking': 'true',
                  'Acquire::ForceHash': 'SHA256', 'APT::Architecture': 'amd64',
                  'Dir::Bin::dpkg': '/usr/bin/dpkg', 'Dir::Bin::methods': '/usr/lib/apt/methods',
                  'APT::Solver': 'internal', 'APT::Planner': 'internal',
                  'APT::Get::AllowUnauthenticated': 'false', 'APT::Get::Assume-Yes': 'false'}
    argv = ['/usr/bin/apt-get', '-c', str(final)]
    for key, value in selections.items():
        argv += ['-o', key + '=' + value]
    argv += ['--print-uris', '--no-remove', 'install', '--', *packages]
    printed = run(argv, workspace, 'print-uris', timeout=180, env=env).decode()
    remote, local = [], []
    for directory in (BUILD / 'config/packages.chroot', BUILD / 'config/packages'):
        if directory.exists():
            for package_path in sorted(directory.glob('*.deb')):
                local.append(dict(evidence(package_path, 64 * 1024 * 1024),
                                  kind='local-build-input', host_download=False))
    for line in printed.splitlines():
        if not line.startswith("'"):
            continue
        match = re.fullmatch(r"'([^']+)' ([^\s/]+) ([0-9]+) SHA256:([0-9a-f]{64})", line)
        if not match:
            raise ValueError('APT URI without complete SHA256: ' + line[:300])
        url, filename, size, sha = match.groups()
        uri = urlsplit(url)
        if uri.scheme == 'file':
            local.append({'url': url, 'filename': filename, 'size': int(size), 'sha256': sha})
            continue
        if uri.hostname not in ('deb.debian.org', 'security.debian.org') or uri.port is not None or not uri.path.startswith(('/debian/pool/', '/debian-security/pool/')):
            raise ValueError('Remote URI is outside reviewed Debian archives')
        if uri.scheme not in ('http', 'https') or uri.username or uri.password or uri.query or uri.fragment:
            raise ValueError('Unsupported remote URI')
        candidates = [r for r in by_sha.get(sha, []) if unquote(uri.path).endswith('/' + r['Filename'])
                      and r['Size'] == size and r['SHA256'] == sha]
        identities = {(r['Package'], r['Version']) for r in candidates}
        if len(identities) != 1 or not re.fullmatch(r'[A-Za-z0-9+.%:~_-]+\.deb', filename):
            raise ValueError('URI does not identify one signed target package: ' + filename)
        package, version = identities.pop()
        remote.append(dict(url=url, filename=filename, size=int(size), sha256=sha, package=package, version=version))
    if len(remote) > 4096 or len({p['filename'] for p in remote}) != len(remote):
        raise ValueError('Oversized plan or duplicate archive basename')
    for release in signed:
        if evidence(release['inrelease']['path'], 8 * 1024 * 1024) != release['inrelease']:
            raise ValueError('Signed release changed during planning')
        for index in release['indexes']:
            current = evidence(index['path'], 256 * 1024 * 1024)
            if any(current[k] != index[k] for k in current):
                raise ValueError('Package index changed during planning')
    if provenance() != before or evidence(queue, 128 * 1024)['sha256'] != digest(raw):
        raise ValueError('Target state changed during planning')
    result = dict(schema=1, nonce=args.nonce, planning_only=True, packages=remote, local_packages=local,
                  created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  selection=dict(path=str(queue), sha256=digest(raw), count=len(packages)),
                  coverage=dict(remote_uri_count=len(remote), sha256_count=len(remote), local_input_count=len(local),
                                all_remote_uris_matched_signed_catalog=True,
                                note='APT omits already cached archives; plan covers this print-uris transaction only.'),
                  provenance=before, signed_catalogs=signed, verification_keyring=keyring,
                  apt_options=selections, print_uris_sha256=digest(printed.encode()))
    data = (json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n').encode()
    if len(data) > MAX:
        raise ValueError('Plan exceeds 2 MiB')
    target = OUT / 'package-download-plan.json'
    # Do not overwrite another nonce's result or stale output.
    with target.open('xb') as stream:
        stream.write(data)
    print('Exported planning-only manifest:', len(remote), 'remote packages;', len(data), 'bytes')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit('Package plan refused: ' + str(error))
