#!/usr/bin/env python3
"""Guest-only verified cache delivery. Does not run APT, dpkg or live-build."""
import argparse
import ctypes
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import urllib.request

BUILD = Path('/root/windows12-build')
ROOT = BUILD / 'chroot'
OUT = Path('/project-output')
CACHE = ROOT / 'var/cache/apt/archives'
ORIGIN = 'http://10.0.2.2:8765'
MAX_PLAN = 2 * 1024 * 1024
MAX_PACKAGE = 512 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024 * 1024
LOCAL_PAIR_NAME = 'windows12-desktop_0.1.0~preview2_all.deb'
LOCAL_READ_PAIR = frozenset((BUILD / 'config/packages.chroot' / LOCAL_PAIR_NAME,
                             ROOT / 'packages' / LOCAL_PAIR_NAME))
LOCAL_PAIR_SHA256 = '5db8cb011056994620abdfe550a31cbebc492e5a66ce2006551861484adf1776'
HEX = re.compile('[0-9a-f]{64}')
RUNTIME_STAGES = {'chroot_devpts', 'chroot_proc', 'chroot_selinuxfs', 'chroot_sysfs'}
STAGES = {'config', 'bootstrap', 'bootstrap_cache.save', 'chroot_apt',
          'chroot_debianchroot', 'chroot_dpkg', 'chroot_hostname', 'chroot_hosts',
          'chroot_resolv', 'chroot_sysv-rc', 'chroot_archives', 'chroot_firmware',
          'chroot_includes_before_packages', 'chroot_linux-image',
          'chroot_package-lists.install', 'chroot_preseed', 'chroot_devpts',
          'chroot_proc', 'chroot_selinuxfs', 'chroot_sysfs'}


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


def ancestry(path, leaf=True):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts or str(path) != os.path.normpath(str(path)):
        raise ValueError('Noncanonical absolute path')
    for p in reversed((path, *path.parents) if leaf else tuple(path.parents)):
        s = p.lstat()
        if stat.S_ISLNK(s.st_mode) or (p != path and not stat.S_ISDIR(s.st_mode)):
            raise ValueError('Alias or nondirectory ancestor: ' + str(p))
    if path.resolve(strict=leaf) != path:
        raise ValueError('Canonical ancestry mismatch')


def reviewed_read_links(path, info):
    """Read-only exception for live-build's one exact CP_OPTIONS=-l pair."""
    if info.st_nlink == 1:
        return False
    path = Path(path)
    if (path not in LOCAL_READ_PAIR or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 2 or info.st_uid != 0 or info.st_gid != 0
            or info.st_size != 7118):
        raise ValueError('Unreviewed hardlink input: ' + str(path))
    peer = next(p for p in LOCAL_READ_PAIR if p != path)
    ancestry(path)
    ancestry(peer)
    if stable_metadata(peer.lstat()) != stable_metadata(info):
        raise ValueError('Reviewed local hardlink pair identity differs')
    return True


def snapshot(path, limit=MAX_PACKAGE):
    path = Path(path)
    ancestry(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        linked_local = reviewed_read_links(path, before)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ValueError('Not a bounded regular file: ' + str(path))
        h = hashlib.sha256()
        total = 0
        while True:
            data = stream.read(1024 * 1024)
            if not data:
                break
            total += len(data)
            if total > limit:
                raise ValueError('File grew beyond bound')
            h.update(data)
        after = os.fstat(stream.fileno())
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_uid', 'st_gid', 'st_nlink')
    if any(getattr(before, k) != getattr(after, k) for k in fields) or path.lstat() != after:
        raise ValueError('File changed during read: ' + str(path))
    ancestry(path)
    reviewed_read_links(path, after)
    if linked_local and h.hexdigest() != LOCAL_PAIR_SHA256:
        raise ValueError('Reviewed linked package SHA256 differs')
    return dict(path=str(path), size=total, sha256=h.hexdigest(),
                metadata={k: getattr(after, k) for k in fields})


def same(item, limit):
    now = snapshot(item['path'], limit)
    if any(now[k] != item[k] for k in ('path', 'size', 'sha256')):
        raise ValueError('Plan input changed: ' + item['path'])
    return now


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Local delivery redirects forbidden')


# Only these fixed local URLs reach this opener. Environment proxies are disabled.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def receive(path, limit, stream=None):
    if path != '/package-plan.json' and not re.fullmatch('/package-cache/[0-9a-f]{64}\\.deb', path):
        raise ValueError('Nonlocal delivery path')
    h, total, chunks = hashlib.sha256(), 0, []
    deadline = time.monotonic() + 600
    with OPENER.open(ORIGIN + path, timeout=30) as response:
        if response.status != 200 or response.geturl() != ORIGIN + path:
            raise ValueError('Unexpected local response identity')
        length = response.headers.get('Content-Length')
        if length is not None and (not length.isdigit() or int(length) > limit):
            raise ValueError('Invalid response size')
        while True:
            if time.monotonic() > deadline:
                raise ValueError('Delivery time bound exceeded')
            chunk = response.read(min(1024 * 1024, limit - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ValueError('Delivery exceeds bound')
            h.update(chunk)
            if stream is None:
                chunks.append(chunk)
            else:
                stream.write(chunk)
        if length is not None and total != int(length):
            raise ValueError('Response size mismatch')
    return total, h.hexdigest(), b''.join(chunks)


def copy_local(item, stream):
    source = Path(item['source_path'])
    ancestry(source)
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    h, total = hashlib.sha256(), 0
    with os.fdopen(fd, 'rb') as incoming:
        before = os.fstat(incoming.fileno())
        linked_local = reviewed_read_links(source, before)
        if not stat.S_ISREG(before.st_mode) or before.st_size != item['size']:
            raise ValueError('Local source type/size differs')
        while True:
            chunk = incoming.read(min(1024 * 1024, item['size'] - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > item['size']:
                raise ValueError('Local source grew beyond planned size')
            stream.write(chunk)
            h.update(chunk)
        after = os.fstat(incoming.fileno())
    ancestry(source)
    if stable_metadata(before) != stable_metadata(after) or stable_metadata(source.lstat()) != stable_metadata(after):
        raise ValueError('Local source changed during copy')
    reviewed_read_links(source, after)
    if linked_local and h.hexdigest() != LOCAL_PAIR_SHA256:
        raise ValueError('Reviewed linked package changed during copy')
    return total, h.hexdigest(), b''


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON member')
        value[key] = item
    return value


def load_plan(raw, args):
    plan = json.loads(raw, object_pairs_hook=unique_object)
    if plan.get('schema') != 1 or plan.get('planning_only') is not True or plan.get('nonce') != args.plan_nonce:
        raise ValueError('Wrong plan schema, purpose or nonce')
    coverage = plan['coverage']
    if coverage.get('full_transaction') is not True or coverage.get('isolated_empty_archive_cache') is not True:
        raise ValueError('Full transaction from an isolated empty archive cache required')
    remote, local = plan['packages'], plan['local_archives']
    if not isinstance(remote, list) or not isinstance(local, list):
        raise ValueError('Invalid remote/local archive lists')
    packages = remote + local
    if len(packages) > 4096:
        raise ValueError('Oversized package plan')
    names, hashes, total = set(), {}, 0
    for p in packages:
        is_local = 'source_path' in p
        required = ({'filename', 'size', 'sha256', 'source_path', 'target_source_path'} if is_local
                    else {'url', 'filename', 'size', 'sha256', 'package', 'version'})
        if not required.issubset(p) or set(p) - required - ({'target_source_present'} if is_local else set()):
            raise ValueError('Unexpected package fields')
        if is_local != (p in local):
            raise ValueError('Archive delivery kind differs from plan list')
        if not isinstance(p['filename'], str) or not re.fullmatch(r'[A-Za-z0-9+.%:~_-]+\.deb', p['filename']):
            raise ValueError('Unsafe archive basename')
        if not isinstance(p['sha256'], str) or not HEX.fullmatch(p['sha256']):
            raise ValueError('Invalid package SHA256')
        if type(p['size']) is not int or not 0 < p['size'] <= MAX_PACKAGE:
            raise ValueError('Invalid package size')
        if is_local:
            source = Path(p['source_path'])
            target = Path(p['target_source_path'])
            if (str(source) != p['source_path'] or source.parent not in (BUILD / 'config/packages.chroot', BUILD / 'config/packages')
                    or not re.fullmatch(r'[A-Za-z0-9+.%:~_-]+\.deb', source.name)
                    or str(target) != p['target_source_path'] or target.parent != ROOT / 'packages'
                    or not re.fullmatch(r'[A-Za-z0-9+.%:~_-]+\.deb', target.name)):
                raise ValueError('Unexpected local archive source path')
            expected = {k: p[k] for k in ('size', 'sha256')}
            inputs = [i for i in plan['local_packages'] if i.get('kind') == 'local-build-input'
                      and i.get('host_download') is False and i.get('path') == str(source)
                      and all(i.get(k) == v for k, v in expected.items())]
            matches = [i for i in plan['provenance'] if i.get('path') == str(source)
                       and all(i.get(k) == v for k, v in expected.items()) and 'kind' not in i]
            if len(inputs) != 1 or len(matches) != 1:
                raise ValueError('Local archive is not an exact planned config input')
            if 'target_source_present' in p and type(p['target_source_present']) is not bool:
                raise ValueError('Invalid informational local source presence')
        elif not all(isinstance(p[k], str) and 0 < len(p[k]) <= 4096 for k in ('url', 'package', 'version')):
            raise ValueError('Invalid package identity')
        if p['filename'] in names or (p['sha256'] in hashes and hashes[p['sha256']] != p['size']):
            raise ValueError('Duplicate name or conflicting content identity')
        names.add(p['filename'])
        hashes[p['sha256']] = p['size']
        total += p['size']
    if total > MAX_TOTAL:
        raise ValueError('Aggregate package size exceeds 8 GiB')
    return plan


def under(path, directory):
    p = Path(path)
    return str(p) == path and p.is_absolute() and '..' not in p.parts and p.is_relative_to(directory)


def provenance(plan):
    items = plan['provenance']
    if not isinstance(items, list) or not 1 <= len(items) <= 512:
        raise ValueError('Invalid provenance count')
    result, seen, total = [], set(), 0
    allowed_roots = (ROOT / 'etc/apt', BUILD / 'config', BUILD / '.build')
    fixed = {str(ROOT / 'var/lib/dpkg/status'), str(ROOT / 'var/lib/apt/extended_states')}
    for item in items:
        path = item['path']
        if path in seen or not (path in fixed or any(under(path, p) for p in allowed_roots)):
            raise ValueError('Unexpected provenance path')
        seen.add(path)
        if item.get('kind') == 'reviewed-hook-symlink':
            p = Path(path)
            if not under(path, BUILD / 'config/hooks') or len(p.relative_to(BUILD / 'config/hooks').parts) != 2:
                raise ValueError('Unexpected hook path')
            target = '/usr/share/live/build/hooks/' + p.relative_to(BUILD / 'config/hooks').as_posix()
            if target not in EXPECTED_HOOKS or item['target'] != target:
                raise ValueError('Unexpected hook target')
            ancestry(p, leaf=False)
            s = p.lstat()
            if not stat.S_ISLNK(s.st_mode) or s.st_nlink != 1 or os.readlink(p) != target:
                raise ValueError('Hook literal changed')
            ev = item['target_evidence']
            if ev['path'] != target or ev['sha256'] != EXPECTED_HOOKS[target]:
                raise ValueError('Hook evidence identity differs')
            current = same(ev, 1024 * 1024)
            result.append({'link': path, 'target': target, 'metadata': stable_metadata(s), 'evidence': current})
            total += current['size']
        else:
            if set(item) != {'path', 'size', 'sha256'}:
                raise ValueError('Unexpected regular provenance fields')
            current = same(item, 32 * 1024 * 1024)
            total += current['size']
            result.append(current)
    if total > 64 * 1024 * 1024 or str(ROOT / 'var/lib/dpkg/status') not in seen:
        raise ValueError('Oversized or incomplete provenance')
    # Re-enumerate configuration and stage trees, detecting added/removed inputs too.
    actual = set(fixed) & {str(p) for p in map(Path, fixed) if p.exists()}
    count = 0
    for directory in allowed_roots:
        ancestry(directory)
        for p in directory.rglob('*'):
            count += 1
            if count > 4096 or len(p.relative_to(directory).parts) > 16:
                raise ValueError('Provenance traversal exceeds bound')
            s = p.lstat()
            if not stat.S_ISDIR(s.st_mode):
                actual.add(str(p))
    if actual != seen:
        raise ValueError('Provenance membership changed')
    stages = list((BUILD / '.build').iterdir())
    names = {p.name for p in stages}
    if (not (STAGES - RUNTIME_STAGES).issubset(names) or not names.issubset(STAGES)
            or any(not stat.S_ISREG(p.lstat().st_mode) or p.stat().st_size for p in stages)):
        raise ValueError('Expected completed pre-install flags and only optional runtime flags')
    queue = plan['selection']
    if queue['path'] != str(ROOT / 'root/packages.chroot'):
        raise ValueError('Unexpected queue path')
    q = snapshot(queue['path'], 128 * 1024)
    if q['sha256'] != queue['sha256']:
        raise ValueError('Package queue changed')
    result.append(q)
    key = plan['verification_keyring']
    if key['path'] not in {'/usr/share/keyrings/debian-archive-keyring.pgp',
                           '/usr/share/keyrings/debian-archive-keyring.gpg'}:
        raise ValueError('Unexpected verification keyring')
    result.append(same(key, MAX_PLAN))
    catalogs = plan['signed_catalogs']
    if not isinstance(catalogs, list) or not 1 <= len(catalogs) <= 16:
        raise ValueError('Invalid signed catalogs')
    catalog_paths = set()
    for release in catalogs:
        entries = [release['inrelease'], *release['indexes']]
        if len(entries) > 128:
            raise ValueError('Too many indexes')
        for index, item in enumerate(entries):
            path = item['path']
            p = Path(path)
            if p.parent != ROOT / 'var/lib/apt/lists' or str(p) != path or path in catalog_paths:
                raise ValueError('Unexpected catalog path')
            if (index == 0 and not p.name.endswith('_InRelease')) or (index and '_Packages' not in p.name):
                raise ValueError('Unexpected catalog basename')
            catalog_paths.add(path)
            result.append(same(item, 256 * 1024 * 1024 if index else 8 * 1024 * 1024))
    return result


def unchanged_identities(baseline):
    # Cheap between-boundary check; the final full hash catches byte changes.
    # Point-in-time metadata checks do not replace controller job exclusion.
    for entry in baseline:
        if 'link' in entry:
            p = Path(entry['link'])
            ancestry(p, leaf=False)
            if stable_metadata(p.lstat()) != entry['metadata'] or os.readlink(p) != entry['target']:
                raise ValueError('Hook identity changed during import')
            entry = entry['evidence']
        p = Path(entry['path'])
        ancestry(p)
        current = p.lstat()
        if stable_metadata(current) != entry['metadata']:
            raise ValueError('Target input identity changed during import: ' + str(p))
        reviewed_read_links(p, current)


def quiescent():
    mounts = Path('/proc/self/mountinfo').read_bytes()
    if len(mounts) > MAX_PLAN:
        raise ValueError('Oversized mount inventory')
    for line in mounts.splitlines():
        fields = line.split()
        if len(fields) > 4 and (fields[4] == bytes(BUILD) or fields[4].startswith(bytes(BUILD) + b'/')):
            raise ValueError('Target build mount remains active')
    processes = []
    for process in Path('/proc').iterdir():
        processes.append(process)
        if len(processes) > 32768:
            raise ValueError('Process inventory exceeds bound')
    names = {'lb', 'live-build', 'apt', 'apt-get', 'aptitude', 'dpkg', 'dpkg-deb', 'debootstrap'}
    for p in processes:
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            with (p / 'cmdline').open('rb') as stream:
                raw = stream.read(65537)
        except FileNotFoundError:
            continue
        if len(raw) > 65536:
            raise ValueError('Oversized process command')
        args = raw.decode(errors='replace').split('\0')
        if any(Path(a).name in names or a.startswith('/usr/lib/live/build/') for a in args):
            raise ValueError('Active package/build process: ' + p.name)


def inventory():
    ancestry(CACHE)
    entries = []
    for entry in CACHE.iterdir():
        entries.append(entry)
        if len(entries) > 8192:
            raise ValueError('Cache inventory exceeds bound')
    result, total = {}, 0
    for p in sorted(entries):
        s = p.lstat()
        if stat.S_ISLNK(s.st_mode) or s.st_nlink != 1 and not stat.S_ISDIR(s.st_mode):
            raise ValueError('Cache aliases refused')
        if stat.S_ISREG(s.st_mode):
            item = snapshot(p)
            total += item['size']
            if total > MAX_TOTAL:
                raise ValueError('Existing cache exceeds 8 GiB')
            result[p.name] = item
        elif stat.S_ISDIR(s.st_mode) and p.name == 'partial':
            # Never touch partial data; recursively hash it and preserve its metadata.
            children = []
            for child in p.rglob('*'):
                children.append(child)
                if len(children) > 4096 or len(child.relative_to(p).parts) > 16:
                    raise ValueError('Partial inventory exceeds bound')
            records = []
            for child in sorted(children):
                cs = child.lstat()
                if stat.S_ISDIR(cs.st_mode):
                    ancestry(child)
                    records.append({'path': str(child), 'metadata': stable_metadata(cs)})
                else:
                    item = snapshot(child)
                    total += item['size']
                    if total > MAX_TOTAL:
                        raise ValueError('Partial cache exceeds byte bound')
                    records.append(item)
            result[p.name] = {'metadata': stable_metadata(s), 'children': records}
        else:
            raise ValueError('Unexpected cache entry type')
    return result


def stable_metadata(s):
    return {k: getattr(s, k) for k in ('st_dev', 'st_ino', 'st_mode', 'st_uid',
            'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')}


def publish_no_replace(source, target):
    # Linux renameat2(RENAME_NOREPLACE): atomic single-link publication;
    # no overwrite, no fallback to replace or hard-link publication.
    library = ctypes.CDLL(None, use_errno=True)
    rename = library.renameat2
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(target), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(target))


def directory_sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def report_write(report, workspace):
    data = (json.dumps(report, sort_keys=True, separators=(',', ':')) + '\n').encode()
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('Report exceeds bound')
    ancestry(OUT)
    target = OUT / 'package-cache-import.json'
    if target.exists() or target.is_symlink():
        old = snapshot(target, 32 * 1024 * 1024)
        if old['metadata']['st_uid'] != 0:
            raise ValueError('Unsafe previous report')
    temporary = workspace / 'report-next.json'
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)
    directory_sync(OUT)
    # Keep the nonce-specific checkpoint even after a later controller exports
    # and retires the top-level report for a new explicit run.
    checkpoint = workspace / 'checkpoint-next.json'
    with checkpoint.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(checkpoint, workspace / 'report.json')
    directory_sync(workspace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nonce', required=True)
    parser.add_argument('--plan-nonce', required=True)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    if not all(re.fullmatch('[0-9a-f]{32}', n) for n in (args.nonce, args.plan_nonce)) or args.nonce == args.plan_nonce or not HEX.fullmatch(args.manifest_sha256):
        raise ValueError('Fresh import nonce, original plan nonce and exact SHA256 required')
    if os.geteuid() != 0:
        raise ValueError('Guest root required')
    snapshot('/run/windows12-build-vm', 4096)
    for p in (BUILD, ROOT, OUT, CACHE):
        ancestry(p)
        if not p.is_dir():
            raise ValueError('Required fixed directory missing')
    target_report = OUT / 'package-cache-import.json'
    if target_report.exists() or target_report.is_symlink():
        raise ValueError('Preserve prior top-level import report before a new run')
    workspace = OUT / ('package-cache-import-' + args.nonce)
    workspace.mkdir(mode=0o700)
    staging = BUILD / ('package-cache-staging-' + args.nonce)
    staging.mkdir(mode=0o700)
    report = dict(schema=1, nonce=args.nonce, plan_nonce=args.plan_nonce,
                  manifest_sha256=args.manifest_sha256, import_performed=False,
                  native_apt_verified=False, installation_verified=False, files=[])
    before = None
    baseline = None
    try:
        report_write(report, workspace)
        size, sha, raw = receive('/package-plan.json', MAX_PLAN)
        if sha != args.manifest_sha256:
            raise ValueError('Manifest SHA256 mismatch')
        plan = load_plan(raw, args)
        quiescent()
        baseline = provenance(plan)
        before = inventory()
        selected = plan['packages'] + plan['local_archives']
        report['files'] = [dict(item, status='not-attempted', delivery=('local-config-copy' if 'source_path' in item else 'local-http')) for item in selected]
        report['cache_before'] = before
        report_write(report, workspace)
        # Full bytes are hashed at import boundaries; cheap stable identities
        # are checked around each individual mutation to avoid O(files*indexes).
        unchanged_identities(baseline)
        publications = 0
        for item, record in zip(selected, report['files']):
            destination = CACHE / item['filename']
            record['status'] = 'pending'
            if destination.exists() or destination.is_symlink():
                found = snapshot(destination)
                if (found['size'], found['sha256']) != (item['size'], item['sha256']):
                    raise ValueError('Existing planned archive differs: ' + item['filename'])
                record.update(status='already-verified', evidence=found)
            else:
                fd, name = tempfile.mkstemp(prefix='archive-', suffix='.part', dir=staging)
                temporary = Path(name)
                with os.fdopen(fd, 'wb') as stream:
                    if 'source_path' in item:
                        length, digest, _ = copy_local(item, stream)
                    else:
                        length, digest, _ = receive('/package-cache/' + item['sha256'] + '.deb', item['size'], stream)
                    if (length, digest) != (item['size'], item['sha256']):
                        raise ValueError('Delivered archive size/SHA256 mismatch')
                    os.fchmod(stream.fileno(), 0o644)
                    os.fchown(stream.fileno(), 0, 0)
                    stream.flush()
                    os.fsync(stream.fileno())
                verified = snapshot(temporary)
                quiescent()
                unchanged_identities(baseline)
                ancestry(CACHE)
                ancestry(staging)
                if snapshot(temporary) != verified:
                    raise ValueError('Staged archive changed before publication')
                publish_no_replace(temporary, destination)
                directory_sync(CACHE)
                directory_sync(staging)
                found = snapshot(destination)
                if (found['size'], found['sha256']) != (item['size'], item['sha256']) or found['metadata']['st_uid'] != 0 or found['metadata']['st_gid'] != 0 or stat.S_IMODE(found['metadata']['st_mode']) != 0o644:
                    raise ValueError('Published archive verification failed')
                ancestry(CACHE)
                unchanged_identities(baseline)
                record.update(status='published-verified', evidence=found)
                publications += 1
                if publications % 25 == 0:
                    report_write(report, workspace)
        after = inventory()
        if any(after.get(name) != entry for name, entry in before.items()):
            raise ValueError('Preexisting cache entry changed')
        for item in selected:
            found = after.get(item['filename'])
            if not isinstance(found, dict) or (found.get('size'), found.get('sha256')) != (item['size'], item['sha256']):
                raise ValueError('Final selected archive differs from authenticated plan: ' + item['filename'])
            info = found.get('metadata', {})
            if (info.get('st_uid'), info.get('st_gid'), info.get('st_nlink')) != (0, 0, 1) or stat.S_IMODE(info.get('st_mode', 0)) != 0o644:
                raise ValueError('Final selected archive metadata differs: ' + item['filename'])
        permitted = set(before) | {p['filename'] for p in selected}
        if set(after) != permitted or provenance(plan) != baseline:
            raise ValueError('Unexpected cache or target state change')
        quiescent()
        report.update(cache_after=after, preserved_target=True, import_performed=True,
                      final_selected_sha256_verified=True, final_verified_archive_count=len(selected))
        report_write(report, workspace)
        print('All selected archive hashes verified; installation has not been performed')
    except Exception as error:
        for record in report['files']:
            if record['status'] == 'pending':
                record['status'] = 'failed'
        report.update(error=str(error)[:2048], import_performed=False)
        if before is not None:
            try:
                after = inventory()
                report['cache_after'] = after
                report['preexisting_cache_preserved'] = all(after.get(n) == e for n, e in before.items())
            except Exception as check_error:
                report['cache_after_error'] = str(check_error)[:1024]
        if baseline is not None:
            try:
                report['preserved_target'] = provenance(plan) == baseline
            except Exception as check_error:
                report['target_after_error'] = str(check_error)[:1024]
        report_write(report, workspace)
        raise


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, http.client.HTTPException) as error:
        raise SystemExit('Package cache import refused: ' + str(error))
