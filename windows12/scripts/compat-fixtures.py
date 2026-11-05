#!/usr/bin/env python3
"""Download/hash-check pinned public Windows QA installers; never execute them.

All inputs, downloads, temporary files and reports remain within windows12.
Notepad++ additionally needs publisher signature verification before execution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/compat'


def safe(path):
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError('Path escapes project: ' + str(path))
    for part in (path, *path.parents):
        if part == ROOT:
            break
        if part.is_symlink():
            raise ValueError('Symlink refused: ' + str(part))
    return path


def check(path, fixture):
    safe(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size != fixture['bytes']:
        raise ValueError('Fixture type/link/size mismatch: ' + path.name)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != fixture['sha256']:
        raise ValueError('Fixture SHA256 mismatch: ' + path.name)
    return digest.hexdigest()


def write_report(report):
    pending = safe(WORK / ('verification.pending-' + str(time.time_ns())))
    with pending.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    pending.replace(safe(WORK / 'verification.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true', help='Check cached files without network')
    parser.add_argument('--list', action='store_true', help='Show pins without downloads')
    args = parser.parse_args()
    started = time.time()
    if not args.list:
        safe(WORK).mkdir(parents=True, exist_ok=True)
        # Invalidate prior success before parsing any verification input. An unsafe
        # output path still fails without writing through it; CLI exit is authoritative.
        write_report({'schema': 1, 'started': started, 'outcome': 'input-validation-incomplete',
                      'hash_verification_passed': False, 'required_publisher_signatures_verified': False,
                      'applications_executed': False, 'compatibility_verified': False})
    lock_path = safe(ROOT / 'build/compat-fixtures.lock.json')
    locked = lock_path.read_bytes()
    lock = json.loads(locked)
    if lock.get('schema') != 1 or not isinstance(lock.get('fixtures'), list) or not lock['fixtures']:
        raise ValueError('Unsupported fixture lock')
    ids, filenames = set(), set()
    for fixture in lock['fixtures']:
        name, identity = fixture['filename'], fixture['id']
        url = urlsplit(fixture['url'])
        if (not re.fullmatch(r'[a-zA-Z0-9_.-]+', name) or name.startswith('.') or
                not name.endswith(('.exe', '.msi')) or name in filenames or identity in ids or
                not re.fullmatch(r'[a-z0-9-]+', identity) or
                type(fixture['bytes']) is not int or not 0 < fixture['bytes'] <= 32 * 1024 * 1024 or
                not re.fullmatch(r'[0-9a-f]{64}', fixture['sha256']) or
                url.scheme != 'https' or url.netloc != 'github.com' or url.query or url.fragment or
                url.path.rsplit('/', 1)[-1] != name or not any(url.path.startswith(prefix) for prefix in
                    ('/ip7z/7zip/releases/download/', '/notepad-plus-plus/notepad-plus-plus/releases/download/'))):
            raise ValueError('Unsafe or duplicate fixture lock entry')
        ids.add(identity)
        filenames.add(name)
        if type(fixture.get('signature_required')) is not bool:
            raise ValueError('Explicit signature requirement needed')
        if fixture['signature_required']:
            key, signature = fixture['publisher_key'], fixture['signature']
            if (key.get('fingerprint') != '14BCE4362749B2B51F8C71226C429F1D8D84F46E' or
                    key.get('url') != 'https://raw.githubusercontent.com/notepad-plus-plus/notepad-plus-plus/v8.9.8.1/nppGpgPub.asc' or
                    key.get('filename') != 'nppGpgPub.asc' or signature.get('url') != fixture['url'] + '.sig' or
                    signature.get('filename') != name + '.sig'):
                raise ValueError('Unexpected publisher verification input')
            for auxiliary in (key, signature):
                if (type(auxiliary['bytes']) is not int or not 0 < auxiliary['bytes'] <= 1024 * 1024 or
                        not re.fullmatch(r'[0-9a-f]{64}', auxiliary['sha256'])):
                    raise ValueError('Invalid publisher input size/hash')
    if args.list:
        print(json.dumps(lock, indent=2))
        return
    safe(WORK).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for key, name in [('HOME', 'home'), ('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'),
                      ('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data')]:
        directory = safe(WORK / name)
        directory.mkdir(exist_ok=True)
        env[key] = str(directory)
    def acquire(fixture):
        target = safe(WORK / fixture['filename'])
        if not target.exists():
            if args.verify_only:
                raise ValueError('Missing cached fixture: ' + target.name)
            partial = safe(WORK / (fixture['filename'] + '.part-' + str(time.time_ns())))
            with partial.open('xb'):
                pass
            subprocess.run(['curl', '--fail', '--location', '--proto', '=https',
                            '--proto-redir', '=https', '--connect-timeout', '20', '--max-time', '180',
                            '--max-filesize', str(fixture['bytes']), '--output', str(partial), fixture['url']],
                           env=env, check=True)
            check(partial, fixture)
            partial.replace(target)
        check(target, fixture)
        return target

    report = {'schema': 1, 'lock_sha256': hashlib.sha256(locked).hexdigest(),
              'started': started, 'outcome': 'verifying', 'hash_verification_passed': False,
              'publisher_signatures_verified': False, 'applications_executed': False,
              'compatibility_verified': False, 'fixtures': []}
    destination = safe(WORK / 'verification.json')
    try:
        for fixture in lock['fixtures']:
            target = acquire(fixture)
            digest = check(target, fixture)
            verified_signature = False
            if fixture['signature_required']:
                key, signature = fixture['publisher_key'], fixture['signature']
                verifier = shutil.which('sqv')
                if not verifier:
                    raise ValueError('Existing sqv required for publisher signature verification; no host install attempted')
                public_key = acquire(key)
                detached = acquire(signature)
                result = subprocess.run([verifier, '--keyring', str(public_key), '--signature-file',
                                         str(detached), str(target)], env=env, check=True,
                                        capture_output=True, text=True, timeout=30)
                if result.stdout.split() != [key['fingerprint']]:
                    raise ValueError('Publisher fingerprint mismatch')
                verified_signature = True
            report['fixtures'].append({'id': fixture['id'], 'path': str(target.relative_to(ROOT)),
                                       'bytes': fixture['bytes'], 'sha256': digest,
                                       'publisher_signature_verified': verified_signature,
                                       'signature_required_before_execution': fixture['signature_required']})
        report['hash_verification_passed'] = True
        report['required_publisher_signatures_verified'] = True
        report['outcome'] = 'verified'
    except Exception as error:
        report['error'] = str(error)
        report['outcome'] = 'failed'
        raise
    finally:
        report['finished'] = time.time()
        write_report(report)
    print(destination)
    print('Pinned bytes verified; no Windows application executed or compatibility certified.')


if __name__ == '__main__':
    main()
