#!/usr/bin/env python3
"""Capture a contained BIOS live-ISO boot with project-local QEMU TCG.
Success means captures were collected, never that the guest booted or installed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / '.work/builder/tools'


def contained(path):
    result = Path(path).resolve()
    if not result.is_relative_to(ROOT) or result == ROOT:
        raise ValueError(f'Path must stay beneath {ROOT}: {path}')
    if any(char in str(result) for char in (',', '\n', '\r', '\x00')):
        raise ValueError('Runtime paths cannot contain commas or control separators')
    return result


class QMP:
    """One FIFO reader/writer; QEMU events and replies share this client."""
    def __init__(self, prefix, events):
        self.prefix = prefix
        self.events = events
        self.buffer = b''
        self.sequence = 0
        for suffix in ('.in', '.out'):
            os.mkfifo(str(prefix) + suffix, 0o600)
        # RDWR prevents FIFO startup deadlock; NONBLOCK permits bounded reads.
        self.writer = os.open(str(prefix) + '.in', os.O_RDWR | os.O_NONBLOCK)
        self.reader = os.open(str(prefix) + '.out', os.O_RDWR | os.O_NONBLOCK)

    def receive(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            if b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                if line.strip():
                    message = json.loads(line)
                    self.events.write(json.dumps(message) + '\n')
                    self.events.flush()
                    return message
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('QMP response timed out')
            readable, _, _ = select.select([self.reader], [], [], remaining)
            if readable:
                self.buffer += os.read(self.reader, 65536)

    def handshake(self):
        message = self.receive(45)
        if 'QMP' not in message:
            raise RuntimeError('Missing QMP greeting')
        self.command('qmp_capabilities')

    def command(self, name, arguments=None):
        self.sequence += 1
        payload = {'execute': name, 'id': self.sequence}
        if arguments is not None:
            payload['arguments'] = arguments
        data = (json.dumps(payload) + '\n').encode()
        written = os.write(self.writer, data)
        if written != len(data):
            raise RuntimeError('Incomplete QMP command write')
        deadline = time.monotonic() + 20
        while True:
            message = self.receive(max(0, deadline - time.monotonic()))
            if message.get('id') == self.sequence:
                if 'error' in message:
                    raise RuntimeError(f'QMP {name}: {message["error"]}')
                return message.get('return')

    def close(self):
        os.close(self.writer)
        os.close(self.reader)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path, help='Existing project-contained ISO')
    parser.add_argument('--output', type=Path, help='New directory beneath project; never reused')
    parser.add_argument('--timeout', type=int, default=300, help='Capture duration in seconds, default 300')
    parser.add_argument('--interval', type=int, default=30, help='Seconds between captures, default 30')
    parser.add_argument('--memory', type=int, default=4096, help='Guest RAM in MiB, default 4096')
    parser.add_argument('--installer-disk-size', help='Attach a NEW disposable qcow2, e.g. 24G; does not install')
    args = parser.parse_args()
    if args.timeout < 1 or args.interval < 1 or args.memory < 512:
        parser.error('timeout/interval must be positive and memory at least 512 MiB')
    if args.installer_disk_size and not re.fullmatch(r'[1-9][0-9]*G', args.installer_disk_size):
        parser.error('installer disk size must be a positive integer followed by G')
    iso = contained(args.iso)
    if not iso.is_file() or iso.suffix.lower() != '.iso':
        raise ValueError('ISO must be an existing regular .iso file beneath the project')
    with iso.open('rb') as stream:
        stream.seek(32769)
        if stream.read(5) != b'CD001':
            raise ValueError('Input lacks ISO9660 primary volume signature')
    tools = contained(TOOLS)
    qemu = contained(tools / 'usr/bin/qemu-system-x86_64')
    firmware = contained(tools / 'usr/share/seabios/bios-256k.bin')
    datadir = contained(tools / 'usr/share/qemu')
    if not qemu.is_file() or not firmware.is_file() or not datadir.is_dir():
        raise ValueError('Project QEMU/SeaBIOS tools missing; see scripts/build-tools.py')
    output = contained(args.output or ROOT / 'artifacts' / f'boot-test-{time.time_ns()}')
    if output.exists():
        raise ValueError('Output directory already exists; choose a new path. No files are overwritten.')
    output.mkdir(parents=True, mode=0o700)
    env = os.environ.copy()
    for variable, leaf in {
        'HOME': 'home', 'TMPDIR': 'tmp', 'XDG_CACHE_HOME': 'cache',
        'XDG_CONFIG_HOME': 'config', 'XDG_DATA_HOME': 'data',
        'XDG_STATE_HOME': 'state', 'XDG_RUNTIME_DIR': 'runtime',
    }.items():
        directory = contained(output / leaf)
        directory.mkdir(mode=0o700)
        env[variable] = str(directory)
    lib = tools / 'usr/lib/x86_64-linux-gnu'
    env.update(LD_LIBRARY_PATH=f'{lib}:{tools / "lib/x86_64-linux-gnu"}',
               QEMU_MODULE_DIR=str(lib / 'qemu'), PYTHONDONTWRITEBYTECODE='1')
    serial = contained(output / 'serial.log')
    serial.touch(exist_ok=False)
    command = [str(qemu), '-machine', 'pc,accel=tcg,smm=off', '-cpu', 'max',
               '-smp', '2', '-m', str(args.memory), '-bios', str(firmware),
               '-L', str(datadir), '-no-user-config', '-nodefaults',
               '-display', 'none', '-monitor', 'none', '-no-reboot',
               '-D', str(contained(output / 'qemu-debug.log')),
               '-device', 'VGA', '-nic', 'none', '-boot', 'order=d,menu=off',
               '-serial', 'file:' + str(serial),
               '-blockdev', json.dumps({'driver': 'file', 'filename': str(iso),
                                       'node-name': 'iso-file', 'read-only': True}),
               '-blockdev', json.dumps({'driver': 'raw', 'file': 'iso-file',
                                       'node-name': 'live-iso', 'read-only': True}),
               '-device', 'ide-cd,drive=live-iso,id=cdrom']
    disk = None
    if args.installer_disk_size:
        qimg = contained(tools / 'usr/bin/qemu-img')
        if not qimg.is_file():
            raise ValueError('Project qemu-img missing')
        disk = contained(output / 'disposable-install.qcow2')
        if disk.exists():
            raise ValueError('Refusing to reuse installer disk')
        with (output / 'disk-create.log').open('w') as disk_log:
            subprocess.run([str(qimg), 'create', '-f', 'qcow2', str(disk), args.installer_disk_size],
                           env=env, cwd=output, check=True, stdout=disk_log, stderr=subprocess.STDOUT)
        command += ['-blockdev', json.dumps({'driver': 'file', 'filename': str(disk), 'node-name': 'disk-file'}),
                    '-blockdev', json.dumps({'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}),
                    '-device', 'virtio-blk-pci,drive=install-disk']
    digest = hashlib.sha256()
    with iso.open('rb') as stream:
        for block in iter(lambda: stream.read(2 ** 20), b''):
            digest.update(block)
    result = {'iso': str(iso), 'iso_sha256': digest.hexdigest(), 'command': command,
              'output': str(output), 'installer_disk': str(disk) if disk else None,
              'boot_verified': False, 'install_verified': False, 'captures': [],
              'started_unix': time.time(), 'outcome': 'starting'}
    process = None
    exit_code = 1
    with (output / 'qmp-events.jsonl').open('w') as events, (output / 'qemu.log').open('w') as log:
        qmp = QMP(contained(output / 'qmp'), events)
        command += ['-qmp', 'pipe:' + str(qmp.prefix)]
        try:
            process = subprocess.Popen(command, env=env, cwd=output, stdout=log, stderr=subprocess.STDOUT)
            result['pid'] = process.pid
            (output / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
            qmp.handshake()
            deadline = time.monotonic() + args.timeout
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f'QEMU exited early with status {process.returncode}; inspect qemu.log')
                status = qmp.command('query-status')
                capture = contained(output / f'screen-{len(result["captures"]):04d}.ppm')
                qmp.command('screendump', {'filename': str(capture)})
                with capture.open('rb') as stream:
                    if stream.read(2) != b'P6':
                        raise RuntimeError('Screenshot is not a binary PPM')
                result['captures'].append({'path': str(capture), 'status': status, 'unix': time.time()})
                (output / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                next_capture = min(deadline, time.monotonic() + args.interval)
                while time.monotonic() < next_capture and process.poll() is None:
                    time.sleep(min(1, max(0, next_capture - time.monotonic())))
            result['outcome'] = 'capture-completed-not-boot-certified'
            exit_code = 0
        except KeyboardInterrupt:
            result['outcome'] = 'interrupted'
            exit_code = 130
        except Exception as error:
            result['outcome'] = 'failed'
            result['error'] = str(error)
            print(str(error), file=sys.stderr)
        finally:
            if process is not None and process.poll() is None:
                try:
                    qmp.command('quit')
                    process.wait(timeout=5)
                except (OSError, TimeoutError, RuntimeError, subprocess.TimeoutExpired):
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=5)
            if process is not None:
                result['qemu_returncode'] = process.poll()
            qmp.close()
            result['finished_unix'] = time.time()
            (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'Capture output: {output}; boot/install remain unverified.')
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
