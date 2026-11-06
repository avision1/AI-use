#!/usr/bin/env python3
"""Host preparation for fixed local package delivery; no fetching or guest work.

Import with source compilation or with bytecode writing disabled. prepare() owns
one nonblocking prefetch lock until close(); callers must close it in finally.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import unquote, urlsplit

MAX_MANIFEST = 2 * 1024 * 1024
MAX_FILE = 512 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024 * 1024
SHA = re.compile(r'[0-9a-f]{64}\Z')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9.+_%:~_-]*\.deb\Z')
IDENTITY = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_gid', 'st_nlink',
            'st_size', 'st_mtime_ns', 'st_ctime_ns')


def _identity(info):
    return tuple(getattr(info, name) for name in IDENTITY)


def _directory(path):
    """Open each absolute component without following links, including ancestors."""
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Canonical absolute directory required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open(path, flags=os.O_RDONLY):
    parent = _directory(path.parent)
    try:
        fd = os.open(path.name, flags | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError('Single-link regular file required: ' + str(path))
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read(path, maximum):
    with os.fdopen(_open(path), 'rb') as stream:
        before = os.fstat(stream.fileno())
        if before.st_size > maximum:
            raise ValueError('Input exceeds size bound: ' + str(path))
        raw = stream.read(maximum + 1)
        if (len(raw) > maximum or len(raw) != before.st_size or
                _identity(before) != _identity(os.fstat(stream.fileno()))):
            raise ValueError('Input changed or exceeded size bound: ' + str(path))
        # Also reject a pathname replacement during the read.
        check = _open(path)
        try:
            if _identity(os.fstat(check)) != _identity(before):
                raise ValueError('Input pathname changed: ' + str(path))
        finally:
            os.close(check)
        return raw


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _json(raw):
    value = json.loads(raw, object_pairs_hook=_unique,
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value


def _url(value):
    if (not isinstance(value, str) or not value.isascii() or len(value) > 2048 or
            any(ord(c) <= 32 or ord(c) == 127 for c in value)):
        raise ValueError('Invalid package URL')
    uri = urlsplit(value)
    if (uri.scheme not in ('http', 'https') or uri.netloc not in
            ('deb.debian.org', 'security.debian.org') or uri.query or uri.fragment or
            '?' in value or '#' in value):
        raise ValueError('Nonofficial package URL')
    if re.search(r'%(?!(?:2[bB]|3[aA]|7[eE]))', uri.path):
        raise ValueError('Unsupported URL escape')
    path = unquote(uri.path)
    roots = (('/debian/pool/', '/debian-security/pool/') if uri.netloc == 'deb.debian.org'
             else ('/debian-security/pool/', '/pool/updates/'))
    if (not path.startswith(roots) or not re.fullmatch(r'/[A-Za-z0-9/_.+~:-]+', path)
            or any(p in ('', '.', '..') for p in path.split('/')[1:])
            or not NAME.fullmatch(path.rsplit('/', 1)[-1])):
        raise ValueError('Unsafe official pool archive path')


def _local_path(value, parents):
    if not isinstance(value, str):
        raise ValueError('Invalid guest local archive path')
    path = Path(value)
    if (str(path) != value or '..' in path.parts or path.parent not in parents or
            len(path.name) > 255 or not NAME.fullmatch(path.name)):
        raise ValueError('Unexpected guest local archive path')


def _plan(raw):
    plan = _json(raw)
    if (type(plan.get('schema')) is not int or plan['schema'] != 1 or
            plan.get('planning_only') is not True or not isinstance(plan.get('nonce'), str)
            or not re.fullmatch(r'[0-9a-f]{32}', plan['nonce'])):
        raise ValueError('Wrong plan schema, purpose or nonce')
    remote, local = plan.get('packages'), plan.get('local_archives')
    coverage = plan.get('coverage')
    if not isinstance(remote, list) or not isinstance(local, list) or len(remote) + len(local) > 4096:
        raise ValueError('Invalid or oversized archive lists')
    if (not isinstance(coverage, dict) or any(coverage.get(k) is not True for k in
            ('full_transaction', 'isolated_empty_archive_cache', 'all_remote_uris_matched_signed_catalog'))):
        raise ValueError('Full signed transaction from isolated empty cache required')
    for key, count in (('remote_uri_count', len(remote)), ('sha256_count', len(remote)),
                       ('local_archive_count', len(local))):
        if type(coverage.get(key)) is not int or coverage[key] != count:
            raise ValueError('Archive coverage count differs: ' + key)
    local_inputs, provenance = plan.get('local_packages'), plan.get('provenance')
    if (not isinstance(local_inputs, list) or not isinstance(provenance, list) or
            len(local_inputs) > 4096 or not 1 <= len(provenance) <= 512 or
            type(coverage.get('local_input_count')) is not int or
            coverage['local_input_count'] != len(local_inputs)):
        raise ValueError('Invalid local input/provenance coverage')
    names, hashes, total = set(), {}, 0
    for is_local, entries in ((False, remote), (True, local)):
        for item in entries:
            fields = ({'filename', 'size', 'sha256', 'source_path', 'target_source_path'} if is_local
                      else {'filename', 'size', 'sha256', 'url', 'package', 'version'})
            if (not isinstance(item, dict) or not fields.issubset(item) or
                    set(item) - fields - ({'target_source_present'} if is_local else set())):
                raise ValueError('Unexpected archive fields')
            name, size, digest = item['filename'], item['size'], item['sha256']
            if (not isinstance(name, str) or len(name) > 255 or not NAME.fullmatch(name) or name in names or
                    type(size) is not int or not 0 < size <= MAX_FILE or
                    not isinstance(digest, str) or not SHA.fullmatch(digest)):
                raise ValueError('Invalid archive filename, size or SHA256')
            if digest in hashes and hashes[digest] != size:
                raise ValueError('Conflicting content-addressed archive sizes')
            names.add(name)
            hashes[digest] = size
            total += size
            if total > MAX_TOTAL:
                raise ValueError('Archive transaction exceeds 8 GiB')
            if is_local:
                build = Path('/root/windows12-build')
                _local_path(item['source_path'], (build / 'config/packages.chroot', build / 'config/packages'))
                _local_path(item['target_source_path'], (build / 'chroot/packages',))
                if 'target_source_present' in item and type(item['target_source_present']) is not bool:
                    raise ValueError('Invalid local archive presence flag')
                same = lambda p: isinstance(p, dict) and p.get('path') == item['source_path'] and all(p.get(k) == item[k] for k in ('size', 'sha256'))
                if (sum(same(p) and p.get('kind') == 'local-build-input' and p.get('host_download') is False for p in local_inputs) != 1 or
                        sum(same(p) and 'kind' not in p for p in provenance) != 1):
                    raise ValueError('Local archive lacks exact config provenance')
            else:
                _url(item['url'])
                for key in ('package', 'version'):
                    value = item[key]
                    if (not isinstance(value, str) or not 0 < len(value) <= 256 or not value.isascii() or
                            any(ord(c) <= 32 or ord(c) == 127 for c in value)):
                        raise ValueError('Invalid package identity')
    return plan


class PreparedInputs:
    """Manifest bytes and verified cache identities protected by prefetch lock."""
    def __init__(self, project, lock_fd, raw, plan, source_sha256):
        self.project = project
        self.lock_fd = lock_fd
        self.raw_manifest = raw
        self.manifest_sha256 = hashlib.sha256(raw).hexdigest()
        self.plan_nonce = plan['nonce']
        self.packages = {}
        self.provenance = dict(manifest_sha256=self.manifest_sha256,
                               plan_nonce=self.plan_nonce, source_sha256=source_sha256,
                               remote_count=len(plan['packages']),
                               bytes=sum(p['size'] for p in plan['packages']),
                               cache_files_verified=0)

    def close(self):
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            self.lock_fd = None

    def _check_lock(self):
        current = _open(self.project / '.work/package-prefetch/prefetch.lock')
        try:
            if _identity(os.fstat(current)) != _identity(os.fstat(self.lock_fd)):
                raise ValueError('Held prefetch lock pathname changed')
        finally:
            os.close(current)

    def open_payload(self, sha):
        """Return (fresh binary stream, size), or None for a nonallowlisted hash."""
        if self.lock_fd is None:
            raise ValueError('Prepared package inputs are closed')
        if not isinstance(sha, str) or sha not in self.packages:
            return None
        self._check_lock()
        item = self.packages[sha]
        fd = _open(item['path'])
        try:
            if _identity(os.fstat(fd)) != item['identity']:
                raise ValueError('Verified package cache identity changed')
            stream = os.fdopen(fd, 'rb')
        except BaseException:
            os.close(fd)
            raise
        return stream, item['size']


def prepare(project: Path, manifest: Path):
    """Validate the complete cache before VM launch; never consult status.json."""
    project, manifest = Path(project), Path(manifest)
    module_root = Path(__file__).absolute().parent.parent
    if (not project.is_absolute() or '..' in project.parts or project != module_root or
            project.resolve(strict=True) != project):
        raise ValueError('Canonical module project root required')
    fd = _directory(project)
    os.close(fd)
    if (not manifest.is_absolute() or '..' in manifest.parts or
            not manifest.is_relative_to(project) or manifest == project):
        raise ValueError('Manifest must be strictly inside project')
    base = project / '.work/package-prefetch'
    # Parent and cache must already exist. The sole permitted creation is lock.
    for directory in (base, base / 'cache'):
        fd = _directory(directory)
        os.close(fd)
    lock = _open(base / 'prefetch.lock', os.O_RDWR | os.O_CREAT)
    result = None
    try:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Prefetch lock is held; package preparation does not wait') from None
        raw = _read(manifest, MAX_MANIFEST)
        plan = _plan(raw)
        run = _json(_read(manifest.parent / 'run.json', MAX_MANIFEST))
        source = _read(project / '.work/builder/build-source.sha256', 65)
        if not re.fullmatch(rb'[0-9a-f]{64}\n?', source):
            raise ValueError('Invalid frozen source SHA256 lock')
        source_sha = source.decode('ascii').strip()
        if (run.get('package_planning') is not True or run.get('planning_nonce') != plan['nonce'] or
                run.get('source_sha256') != source_sha or
                _read(manifest.parent / 'build.exit', 16).strip() != b'0'):
            raise ValueError('Manifest is not bound to a successful matching frozen-source planning run')
        result = PreparedInputs(project, lock, raw, plan, source_sha)
        for item in plan['packages']:
            digest = item['sha256']
            if digest in result.packages:
                continue
            path = base / 'cache' / (digest + '.deb')
            with os.fdopen(_open(path), 'rb') as stream:
                before = os.fstat(stream.fileno())
                if before.st_size != item['size']:
                    raise ValueError('Package cache size mismatch: ' + digest)
                h, remaining = hashlib.sha256(), item['size']
                while remaining:
                    block = stream.read(min(1024 * 1024, remaining))
                    if not block:
                        raise ValueError('Truncated package cache: ' + digest)
                    remaining -= len(block)
                    h.update(block)
                if (stream.read(1) or h.hexdigest() != digest or
                        _identity(before) != _identity(os.fstat(stream.fileno()))):
                    raise ValueError('Package cache SHA256 or stable identity mismatch: ' + digest)
                result.packages[digest] = dict(path=path, size=item['size'], identity=_identity(before))
            # Reopening catches a replaced pathname, without another full hash.
            opened, _ = result.open_payload(digest)
            opened.close()
        # Earlier entries must still have their verified identity after the last
        # archive hash, before the controller is allowed to launch the VM.
        result._check_lock()
        for digest in result.packages:
            opened, _ = result.open_payload(digest)
            opened.close()
        result.provenance['cache_files_verified'] = len(result.packages)
        return result
    except BaseException:
        if result is not None:
            result.close()
        else:
            os.close(lock)
        raise
