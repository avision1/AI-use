#!/usr/bin/env python3
"""Wait for this frozen builder to stop, then audit/capture/install sequentially.

Runs existing reviewed gates. Capture is not a GUI pass. Never controls the
source-builder VM, reuses an installation disk, publishes, or edits the host.
"""
import argparse
import fcntl
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/builder'
BUILD = ROOT / 'artifacts/vm-build'


def safe(path):
    path = Path(path)
    if path.resolve() != Path(os.path.abspath(path)) or not path.resolve().is_relative_to(ROOT):
        raise ValueError('Escaping or symlinked project path refused')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-timeout', type=int, default=14400)
    parser.add_argument('--install', action='store_true', help='Also run the NEW disposable-disk D-I proof')
    args = parser.parse_args()
    if not 60 <= args.wait_timeout <= 14400:
        parser.error('Wait timeout must be60–14400 seconds')
    def interrupted(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupted)
    source = safe(WORK / 'build-source.sha256').read_text().strip()
    if len(source) != 64 or any(c not in '0123456789abcdef' for c in source):
        raise ValueError('Existing frozen source lock required')
    initial = json.loads(safe(BUILD / 'run.json').read_text())
    if initial.get('source_sha256') != source:
        raise ValueError('Build record/source mismatch')
    output = safe(ROOT / 'artifacts' / ('candidate-gates-' + str(time.time_ns())))
    output.mkdir(mode=0o700)
    env = os.environ.copy()
    for key, name in [('HOME', 'home'), ('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'cache'),
                      ('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                      ('XDG_STATE_HOME', 'state'), ('XDG_RUNTIME_DIR', 'runtime')]:
        path = output / name
        path.mkdir(mode=0o700)
        env[key] = str(path)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = {'source_sha256': source, 'started': time.time(), 'stage': 'waiting-for-builder',
              'output': str(output), 'content_audit_verified': False, 'bios_capture_collected': False,
              'install_boot_proof_verified': False, 'gui_verified': False, 'release_verified': False}

    def save():
        pending = safe(output / 'result.pending.json')
        pending.write_text(json.dumps(result, indent=2) + '\n')
        pending.replace(safe(output / 'result.json'))
        print(json.dumps(result), flush=True)

    scripts = ['audit-iso.py', 'boot-test.py', 'install-test.py']
    controller_hashes = {name: hashlib.sha256(safe(ROOT / 'scripts' / name).read_bytes()).hexdigest() for name in scripts}
    result['controller_sha256'] = controller_hashes
    iso_identity = None

    def unchanged():
        if safe(output / 'cancel').exists():
            raise KeyboardInterrupt()
        if json.loads(safe(BUILD / 'run.json').read_text()) != initial or safe(WORK / 'build-source.sha256').read_text().strip() != source:
            raise ValueError('Recorded builder/source changed')
        for name, digest in controller_hashes.items():
            if hashlib.sha256(safe(ROOT / 'scripts' / name).read_bytes()).hexdigest() != digest:
                raise ValueError('Gate controller changed: ' + name)
        if iso_identity is not None:
            info = safe(BUILD / 'windows12-amd64-preview.iso').stat()
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != iso_identity:
                raise ValueError('Candidate ISO changed between gates')

    def gate(name, script, arguments):
        unchanged()
        result['stage'] = name
        save()
        command = [sys.executable, '-B', str(safe(ROOT / 'scripts' / script)), *map(str, arguments)]
        with (output / (name + '.log')).open('x') as log:
            child = None
            try:
                child = subprocess.Popen(command, env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                result['active_helper'] = {'pid': child.pid, 'command': command}
                save()
                while True:
                    try:
                        code = child.wait(timeout=1)
                        break
                    except subprocess.TimeoutExpired:
                        if safe(output / 'cancel').exists():
                            raise KeyboardInterrupt()
            except BaseException:
                if child is not None:
                    if child.poll() is None:
                        try:
                            child.send_signal(signal.SIGINT)
                        except ProcessLookupError:
                            pass
                        except OSError:
                            result['helper_reconciliation_required'] = True
                            raise
                        try:
                            child.wait(timeout=45)
                        except subprocess.TimeoutExpired:
                            result['helper_reconciliation_required'] = True
                            raise RuntimeError('Helper did not stop cooperatively; left alive with its runner lock. Reconcile before further VM work.')
                    if child.returncode is not None and child.returncode < 0:
                        result['helper_reconciliation_required'] = True
                    else:
                        result.pop('active_helper', None)
                raise
            if code < 0:
                result['helper_reconciliation_required'] = True
            else:
                result.pop('active_helper', None)
            if code:
                raise subprocess.CalledProcessError(code, command)
        unchanged()

    save()
    try:
        deadline = time.monotonic() + args.wait_timeout
        while True:
            unchanged()
            current = json.loads(safe(BUILD / 'run.json').read_text())
            if current != initial or safe(WORK / 'build-source.sha256').read_text().strip() != source:
                raise ValueError('Recorded builder/source changed; refusing automatic continuation')
            marker = safe(BUILD / 'build.exit')
            if marker.exists():
                if marker.read_text().strip() != '0':
                    raise ValueError('Builder exported failure; preserve its evidence')
                # Marker is exported before guest shutdown. Wait for the actual
                # supervising runner to release its lock, then let each VM gate
                # independently enforce its own lock/legacy-QMP exclusion.
                with safe(WORK / 'runner.lock').open('r') as lock:
                    try:
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        pass
                    else:
                        break
            if time.monotonic() >= deadline:
                raise TimeoutError('Build wait expired; builder left untouched')
            time.sleep(30)
        archive = safe(WORK / 'checks.tar')
        if archive.stat().st_size > 64 * 1024 * 1024 or hashlib.sha256(archive.read_bytes()).hexdigest() != source:
            raise ValueError('Frozen source bytes changed')
        iso = safe(BUILD / 'windows12-amd64-preview.iso')
        if not iso.is_file() or iso.stat().st_size == 0:
            raise ValueError('No completed ISO')
        info = iso.stat()
        iso_identity = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        gate('iso-audit', 'audit-iso.py', [iso, '--source-archive', archive, '--output', output / 'audit'])
        audit = json.loads((output / 'audit/result.json').read_text())
        if audit.get('audit_passed') is not True or audit.get('source_sha256') != source:
            raise ValueError('Content audit did not pass')
        digest = audit.get('iso_sha256')
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Missing audited ISO digest')
        result['iso_sha256'] = digest
        result['content_audit_verified'] = True
        gate('bios-capture', 'boot-test.py', [iso, '--output', output / 'bios', '--timeout', '300', '--interval', '30'])
        bios = json.loads((output / 'bios/result.json').read_text())
        if bios.get('iso_sha256') != digest or not bios.get('captures'):
            raise ValueError('Missing or mismatched BIOS capture evidence')
        for capture in bios['captures']:
            image = safe(Path(capture['path']))
            if image.parent != output / 'bios' or not image.is_file() or image.stat().st_nlink != 1:
                raise ValueError('Unsafe BIOS capture evidence')
            with image.open('rb') as pixels:
                if pixels.read(3) != b'P6\n' or image.stat().st_size < 32:
                    raise ValueError('Invalid BIOS capture evidence')
        result['bios_capture_collected'] = True
        if args.install:
            gate('install-proof', 'install-test.py', [iso, '--output', output / 'install'])
            proof = json.loads((output / 'install/result.json').read_text())
            if (proof.get('install_verified') is not True or proof.get('disk_boot_verified') is not True
                    or proof.get('iso_sha256') != digest or proof.get('proof_service_one_shot') is not True):
                raise ValueError('Installed-root boot proof did not pass')
            result['install_boot_proof_verified'] = True
        result['stage'] = 'gates-finished-graphical-review-required'
        return 0
    except KeyboardInterrupt:
        result['stage'] = 'interrupted'
        return 130
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result.update(stage='failed', error=str(error))
        return 1
    finally:
        result['finished'] = time.time()
        save()


if __name__ == '__main__':
    sys.exit(main())
