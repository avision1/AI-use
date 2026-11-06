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
# Exact reviewed live-build release hooks; aliases are inventoried, never executed.
EXPECTED_HOOKS = {
    "/usr/share/live/build/hooks/live/0010-disable-kexec-tools.hook.chroot": "fee8b3be4d7beb02e672baafb2d45dcb5019fcbf8f2d4418a789f21f012d88d0",
    "/usr/share/live/build/hooks/live/0050-disable-sysvinit-tmpfs.hook.chroot": "e464e8ef2a17486f0d030d2e4b49fd7808ddd837b715829b3708dc23b542c910",
    "/usr/share/live/build/hooks/normal/1000-create-mtab-symlink.hook.chroot": "c61b7443477c033b7a1674d4cb5f107ae3aba9cf96522fe19c712e2813c574dd",
    "/usr/share/live/build/hooks/normal/1010-enable-cryptsetup.hook.chroot": "97c6adbc9340fc61ca9f7d73ad7f0421a2040a9d97465234300616e125df97c2",
    "/usr/share/live/build/hooks/normal/1020-create-locales-files.hook.chroot": "c1d39733b743f4862fb60b6d46e2686f5696420508fd6dd8f38ea7a4240c6b9d",
    "/usr/share/live/build/hooks/normal/5000-update-apt-file-cache.hook.chroot": "a5fd0c201660ace5e42b0349924e08d4acc3eb5641b718bdb1a2255a63137070",
    "/usr/share/live/build/hooks/normal/5010-update-apt-xapian-index.hook.chroot": "c22027c25636e893b7237d1f18169e207488f7de22649269a8b8873424899639",
    "/usr/share/live/build/hooks/normal/5020-update-glx-alternative.hook.chroot": "8d30b7abab450403d2b563e84280229b181144b587b07d84bcd5a4330990bcd8",
    "/usr/share/live/build/hooks/normal/5030-update-plocate-database.hook.chroot": "6d49216d8567cfdb5efbdae5d7a51a4956c82f34b9dadbd9e35ffe93d103c3d1",
    "/usr/share/live/build/hooks/normal/5040-update-nvidia-alternative.hook.chroot": "5a8a51a4f0422327911320ce5d2ba2cb19308cde411e2d6b36d2badaf5ec3782",
    "/usr/share/live/build/hooks/normal/5050-dracut.hook.chroot": "d93bbc1d07e4adc0117d3257cba4bcf5c0ea75e651e3a5d192859e8c39b5b61f",
    "/usr/share/live/build/hooks/normal/8000-remove-adjtime-configuration.hook.chroot": "28459f07aeee024c3b27319d825107dde4a924fa421ad94b21cdbbd6ddcf0236",
    "/usr/share/live/build/hooks/normal/8010-remove-backup-files.hook.chroot": "ff9b0b3acc6da035d244f6b3f4207defa10efec86faa6cb177921e02c11bde15",
    "/usr/share/live/build/hooks/normal/8020-remove-dbus-machine-id.hook.chroot": "3628dde00fb7aea9be4ed36afccf03928ca89a873b8822bbfebcbf5c0f0cd5ed",
    "/usr/share/live/build/hooks/normal/8030-truncate-log-files.hook.chroot": "034e22076e493384ba588c79eef577222775218b601d33c356424c5ce444b63d",
    "/usr/share/live/build/hooks/normal/8040-remove-mdadm-configuration.hook.chroot": "e8ed438565ecd1bbb5ce057ad60ab8cbefe4be5058e93fc74126a07ae1da601d",
    "/usr/share/live/build/hooks/normal/8050-remove-openssh-server-host-keys.hook.chroot": "dafcf58b1e78e545dcc0dd257fb024d8468650fe70b693ec3e63d6d23f56499e",
    "/usr/share/live/build/hooks/normal/8060-remove-systemd-machine-id.hook.chroot": "ca5f55bb939986ba0130a3516e3d0e4dc882cf0a8e1faa99a522d89d21bc208d",
    "/usr/share/live/build/hooks/normal/8070-remove-temporary-files.hook.chroot": "bc1f1a27053f428fd61417069ba7368090a80121d412acc9e21b2587b7d37571",
    "/usr/share/live/build/hooks/normal/8080-reproducible-glibc.hook.chroot": "1c8724bfad32cde5426a7af487aecff4cf6778b54837df4424fa0a237aa4b888",
    "/usr/share/live/build/hooks/normal/8090-remove-ssl-cert-snakeoil.hook.chroot": "1c5a6f27be4386aa144a80f9fbd8efc92219de7c0822ce5faed713f6a563ccc8",
    "/usr/share/live/build/hooks/normal/8100-remove-udev-persistent-cd-rules.hook.chroot": "ca525ec0887ba3f89f17efd8c1a64457dc077e8127938f0a1cac85b305b00e48",
    "/usr/share/live/build/hooks/normal/8110-remove-udev-persistent-net-rules.hook.chroot": "b135ecd88708d705c9e48a211b53a805795d406820888c93236d1ac66436ed0b",
    "/usr/share/live/build/hooks/normal/9000-remove-gnome-icon-cache.hook.chroot": "c6770f96ff70861dfb1fd716205108c24029a876b8124819755866d22bdfb8d8",
    "/usr/share/live/build/hooks/normal/9010-remove-python-pyc.hook.chroot": "dbad666c84484afe5d1c2e55aca0be0db281f6a1b957665488a0580997effb7a",
    "/usr/share/live/build/hooks/normal/9020-remove-man-cache.hook.chroot": "19b09d42c75108c5cf14f6a5b524da89d96f34c970104314cb7eef755d9ae043"
}


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
    hook_links = []
    hook_bytes = 0
    for directory in [ROOT / 'etc/apt', BUILD / 'config', BUILD / '.build']:
        if directory.exists():
            for p in directory.rglob('*'):
                visited += 1
                if visited > 4096 or len(p.relative_to(directory).parts) > 16:
                    raise ValueError('Provenance traversal exceeds bounded scope')
                info = p.lstat()
                if stat.S_ISLNK(info.st_mode):
                    relative = p.relative_to(BUILD / 'config/hooks') if p.is_relative_to(BUILD / 'config/hooks') else None
                    if relative is None or len(relative.parts) != 2:
                        raise ValueError('Unreviewed provenance alias: ' + str(p))
                    expected = '/usr/share/live/build/hooks/' + relative.as_posix()
                    if expected not in EXPECTED_HOOKS or os.readlink(p) != expected:
                        raise ValueError('Unreviewed hook alias target: ' + str(p))
                    target = evidence(expected, 1024 * 1024)
                    if target['sha256'] != EXPECTED_HOOKS[expected]:
                        raise ValueError('Installed hook differs from reviewed source: ' + expected)
                    hook_bytes += target['size']
                    if hook_bytes > 64 * 1024 * 1024:
                        raise ValueError('Hook provenance bytes exceed bound')
                    hook_links.append({'path': str(p), 'kind': 'reviewed-hook-symlink', 'target': expected, 'target_evidence': target})
                    if len(paths) + len(hook_links) > 512:
                        raise ValueError('Too many provenance files')
                    continue
                if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                    raise ValueError('Unsupported provenance path type: ' + str(p))
                if stat.S_ISREG(info.st_mode):
                    paths.append(p)
                    if len(paths) + len(hook_links) > 512:
                        raise ValueError('Too many provenance files')
    result, total = [], hook_bytes
    for p in sorted(set(paths)):
        if p.exists():
            item = evidence(p, 32 * 1024 * 1024)
            total += item['size']
            if total > 64 * 1024 * 1024:
                raise ValueError('Provenance bytes exceed bound')
            result.append(item)
    return sorted(result + hook_links, key=lambda item: item['path'])


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
        roots = {'deb.debian.org': ('/debian/pool/', '/debian-security/pool/'),
                 'security.debian.org': ('/debian-security/pool/', '/pool/updates/')}
        if uri.hostname not in roots or uri.port is not None or not uri.path.startswith(roots[uri.hostname]):
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
