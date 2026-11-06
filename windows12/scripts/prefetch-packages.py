#!/usr/bin/env python3
"""Fetch a bounded batch of manifest-pinned Debian inputs; never install them.

Example: python3 -B scripts/prefetch-packages.py artifacts/plan/package-download-plan.json --expected-nonce FRESH32HEX
Repeat the same command to verify cached inputs and fetch the next <=100 files.
The guest exporter authenticates the plan's inputs; this consumer validates its
shape, origins, sizes and hashes, but does not itself authenticate APT metadata.
"""
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import threading
from urllib.parse import unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / '.work/package-prefetch'
MAX_MANIFEST = 8 * 1024 * 1024
MAX_FILE = 512 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024 * 1024
SHA = re.compile(r'[0-9a-f]{64}\Z')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9.+_~%:-]*\.deb\Z')


def project_path(value):
    path = Path(os.path.abspath(value))
    try:
        path.relative_to(ROOT)
    except ValueError:
        raise ValueError('path must be beneath the project') from None
    for part in [path, *path.parents]:
        if part == ROOT.parent:
            break
        if part.is_symlink():
            raise ValueError('symlink path refused')
    return path


def directory(path):
    path = project_path(path)
    if path == ROOT:
        return
    directory(path.parent)
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    if not stat.S_ISDIR(path.lstat().st_mode):
        raise ValueError('non-directory path refused')


def open_regular(path, flags=os.O_RDONLY, mode=0o600):
    path = project_path(path)
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, mode)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise ValueError('only single-link regular files are allowed')
    return fd


def read_bounded(path, maximum):
    fd = open_regular(path)
    with os.fdopen(fd, 'rb') as stream:
        if os.fstat(stream.fileno()).st_size > maximum:
            raise ValueError('input exceeds size bound')
        data = stream.read(maximum + 1)
        if len(data) > maximum:
            raise ValueError('input exceeds size bound')
        return data


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def canonical_url(value):
    if (not isinstance(value, str) or not value.isascii() or len(value) > 2048 or
            any(ord(c) <= 32 or ord(c) == 127 for c in value)):
        raise ValueError('invalid package URL')
    parsed = urlsplit(value)
    if (parsed.scheme not in ('http', 'https') or parsed.netloc not in
            ('deb.debian.org', 'security.debian.org') or parsed.query or
            parsed.fragment or '?' in value or '#' in value):
        raise ValueError('package URL origin/authority/query refused')
    original_path = parsed.path
    # APT escapes '+' in legitimate Debian versions, and can escape epoch ':'
    # or '~'. Admit only these escapes; encoded separators, dots, percent signs,
    # controls and double encoding are refused rather than normalized away.
    if re.search(r'%(?!(?:2[bB]|3[aA]|7[eE]))', original_path):
        raise ValueError('unsupported URL path escape')
    path = unquote(original_path)
    if ('%' in path or not path.isascii() or '\\' in path or
            any(piece in ('', '.', '..') for piece in path.split('/')[1:])):
        raise ValueError('noncanonical package URL path')
    prefixes = ('/debian/pool/', '/debian-security/pool/') if parsed.netloc == 'deb.debian.org' else ('/debian-security/pool/',)
    if not path.startswith(prefixes) or not NAME.fullmatch(path.rsplit('/', 1)[-1]):
        raise ValueError('package URL is not an official pool .deb path')
    if not re.fullmatch(r'/[A-Za-z0-9/_.+~:-]+', path):
        raise ValueError('invalid pool path characters')
    return urlunsplit(('https', parsed.netloc, original_path, '', ''))


def manifest(path):
    raw = read_bounded(path, MAX_MANIFEST)
    data = json.loads(raw, object_pairs_hook=unique_keys)
    if (not isinstance(data, dict) or type(data.get('schema')) is not int or
            data['schema'] != 1 or data.get('planning_only') is not True or
            not isinstance(data.get('nonce'), str) or
            not re.fullmatch(r'[0-9a-f]{32}', data['nonce'])):
        raise ValueError('invalid schema, planning_only flag or nonce')
    packages = data.get('packages')
    if not isinstance(packages, list) or len(packages) > 4096:
        raise ValueError('packages must be a list of at most 4096 entries')
    names, hashes, total, validated = set(), {}, 0, []
    for item in packages:
        if not isinstance(item, dict):
            raise ValueError('invalid package entry')
        name, size, digest = item.get('filename'), item.get('size'), item.get('sha256')
        if (not isinstance(name, str) or len(name) > 255 or not NAME.fullmatch(name) or
                '/' in name or '\\' in name or name in names):
            raise ValueError('invalid or duplicate package filename')
        if type(size) is not int or not 0 < size <= MAX_FILE:
            raise ValueError('invalid package size')
        if not isinstance(digest, str) or not SHA.fullmatch(digest):
            raise ValueError('invalid package SHA256')
        for field in ('package', 'version'):
            if (not isinstance(item.get(field), str) or not item[field] or
                    len(item[field]) > 256 or not item[field].isascii() or
                    any(ord(c) < 33 or ord(c) == 127 for c in item[field])):
                raise ValueError('invalid package identity')
        url = canonical_url(item.get('url'))
        if digest in hashes and hashes[digest] != size:
            raise ValueError('inconsistent content-addressed size')
        names.add(name)
        hashes[digest] = size
        total += size
        if total > MAX_TOTAL:
            raise ValueError('manifest exceeds 8 GiB')
        validated.append(dict(item, url=url))
    return data['nonce'], hashlib.sha256(raw).hexdigest(), validated, total


def verified_fd(fd, item):
    before = os.fstat(fd)
    if before.st_size != item['size'] or before.st_nlink != 1 or not stat.S_ISREG(before.st_mode):
        return False
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    remaining = item['size']
    while remaining:
        block = os.read(fd, min(1024 * 1024, remaining))
        if not block:
            return False
        remaining -= len(block)
        digest.update(block)
    after = os.fstat(fd)
    return (digest.hexdigest() == item['sha256'] and
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns))


def cached(item):
    path = BASE / 'cache' / (item['sha256'] + '.deb')
    try:
        fd = open_regular(path)
    except FileNotFoundError:
        return False
    try:
        if not verified_fd(fd, item):
            raise ValueError('existing cache entry failed size/SHA256 verification')
        return True
    finally:
        os.close(fd)


def atomic_report(report):
    content = (json.dumps(report, sort_keys=True, indent=2) + '\n').encode()
    if len(content) > 2 * 1024 * 1024:
        raise ValueError('report exceeds bound')
    target = BASE / 'status.json'
    if target.exists() or target.is_symlink():
        fd = open_regular(target)
        os.close(fd)
    temporary = BASE / ('status-%d.tmp' % os.getpid())
    fd = open_regular(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(BASE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def download(item, environment, stop):
    if stop.is_set():
        return {'sha256': item['sha256'], 'state': 'deferred'}
    path = BASE / 'cache' / (item['sha256'] + '.part')
    destination = path.with_suffix('.deb')
    fd = open_regular(path, os.O_RDWR | os.O_CREAT)
    try:
        size = os.fstat(fd).st_size
        if size > item['size']:
            raise ValueError('partial file exceeds declared size')
        if not (size == item['size'] and verified_fd(fd, item)):
            if size == item['size']:
                # A complete wrong-hash partial is never resumed or published.
                raise ValueError('complete partial failed SHA256 verification')
            command = ['curl', '-q', '--silent', '--fail', '--proto', '=https',
                       '--proto-redir', '=https', '--connect-timeout', '20',
                       '--max-time', '120', '--retry', '1', '--retry-max-time', '150',
                       '--max-filesize', str(item['size']), '--continue-at', '-',
                       '--output', '/proc/self/fd/%d' % fd,
                       '--write-out', '%{http_code} %{http_connect}', item['url']]
            ca = environment.get('CODEX_PROXY_CERT') or environment.get('CURL_CA_BUNDLE')
            if ca:
                command[2:2] = ['--cacert', ca]
            try:
                result = subprocess.run(command, env=environment, pass_fds=(fd,),
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        timeout=280, check=False)
            except subprocess.TimeoutExpired:
                return {'sha256': item['sha256'], 'state': 'failed', 'error': 'curl timeout'}
            codes = result.stdout.decode('ascii', errors='replace').strip().split()
            status = codes[0] if codes else '000'
            connect_status = codes[1] if len(codes) == 2 else '000'
            if status in ('401', '403', '407') or connect_status in ('401', '403', '407'):
                stop.set()
            if result.returncode != 0 or status not in ('200', '206'):
                return {'sha256': item['sha256'], 'state': 'failed',
                        'curl_exit': result.returncode, 'http_status': status[:16],
                        'proxy_connect_status': connect_status[:16]}
        if not verified_fd(fd, item):
            return {'sha256': item['sha256'], 'state': 'failed', 'error': 'size/SHA256 mismatch'}
        os.fsync(fd)
        current = path.lstat()
        opened = os.fstat(fd)
        if (current.st_dev, current.st_ino, current.st_nlink) != (opened.st_dev, opened.st_ino, 1):
            raise ValueError('partial path changed during transfer')
        if destination.exists() or destination.is_symlink():
            raise ValueError('cache destination appeared during transfer')
        os.replace(path, destination)
        cache_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(cache_fd)
        finally:
            os.close(cache_fd)
        return {'sha256': item['sha256'], 'state': 'downloaded'}
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--expected-nonce', required=True, help='fresh planning_nonce from the matching controller run.json')
    parser.add_argument('--limit', type=int, default=100, help='new downloads, 1..100 (default 100)')
    parser.add_argument('--workers', type=int, default=4, help='parallel transfers, 1..8')
    parser.add_argument('--offline', action='store_true', help='verify existing cache only')
    args = parser.parse_args()
    if not 1 <= args.limit <= 100 or not 1 <= args.workers <= 8:
        parser.error('limit must be 1..100 and workers 1..8')
    if not re.fullmatch(r'[0-9a-f]{32}', args.expected_nonce):
        parser.error('--expected-nonce must be32lowercasehex')
    for folder in (BASE, BASE / 'cache', BASE / 'home', BASE / 'tmp', BASE / 'xdg'):
        directory(folder)
    lock = open_regular(BASE / 'prefetch.lock', os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock)
        raise ValueError('another prefetch invocation holds the lock') from None
    try:
        atomic_report({'schema': 1, 'nonce': args.expected_nonce, 'complete': False,
                       'stage': 'validating-manifest', 'offline': args.offline})
        nonce, manifest_sha, packages, total = manifest(args.manifest)
        if nonce != args.expected_nonce:
            raise ValueError('manifest nonce differs from the expected controller run')
        verified = [item for item in packages if cached(item)]
        initially_present = {item['sha256'] for item in verified}
        present = set(initially_present)
        pending = [item for item in packages if item['sha256'] not in present]
        # One transfer per content hash, even if separate package names share it.
        selected = list({item['sha256']: item for item in pending}.values())[:args.limit]
        report = {'schema': 1, 'nonce': nonce, 'manifest_sha256': manifest_sha,
                  'verified_inputs': len(packages), 'input_bytes': total,
                  'cached': len(verified), 'downloaded': 0, 'pending': len(pending),
                  'complete': not pending, 'offline': args.offline, 'results': [],
                  'stopped_on_auth': False}
        atomic_report(report)
        environment = dict(os.environ)
        environment.pop('SSLKEYLOGFILE', None)
        environment.update(HOME=str(BASE / 'home'), TMPDIR=str(BASE / 'tmp'),
                           TMP=str(BASE / 'tmp'), TEMP=str(BASE / 'tmp'),
                           XDG_CACHE_HOME=str(BASE / 'xdg'), XDG_CONFIG_HOME=str(BASE / 'xdg'),
                           XDG_DATA_HOME=str(BASE / 'xdg'), XDG_STATE_HOME=str(BASE / 'xdg'),
                           XDG_RUNTIME_DIR=str(BASE / 'tmp'))
        stop = threading.Event()
        if not args.offline:
            # Keep only workers tasks in flight; queued requests cannot race
            # ahead after an authentication denial stops the batch.
            iterator = iter(selected)
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
                active = {}
                def submit():
                    if stop.is_set():
                        return
                    item = next(iterator, None)
                    if item is not None:
                        active[pool.submit(download, item, environment, stop)] = item
                for _ in range(args.workers):
                    submit()
                while active:
                    done, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in done:
                        item = active.pop(future)
                        try:
                            outcome = future.result()
                        except (OSError, ValueError) as error:
                            # Never include subprocess environment or raw URLs.
                            outcome = {'sha256': item['sha256'], 'state': 'failed',
                                       'error': type(error).__name__ + ': ' + str(error)[:180]}
                        report['results'].append(outcome)
                        if outcome['state'] == 'downloaded':
                            present.add(item['sha256'])
                        report['downloaded'] = sum(x['sha256'] in present and x['sha256'] not in
                            initially_present for x in packages)
                        report['pending'] = sum(x['sha256'] not in present for x in packages)
                        report['complete'] = report['pending'] == 0
                        report['stopped_on_auth'] = stop.is_set()
                        atomic_report(report)
                        submit()
        print('verified=%d cached=%d downloaded=%d pending=%d complete=%s stopped_on_auth=%s' %
              (report['verified_inputs'], report['cached'], report['downloaded'],
               report['pending'], report['complete'], report['stopped_on_auth']))
        return 0 if report['complete'] else 2
    finally:
        os.close(lock)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print('prefetch refused: %s' % str(error)[:240], file=sys.stderr)
        sys.exit(1)
