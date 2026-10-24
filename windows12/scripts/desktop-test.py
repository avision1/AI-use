#!/usr/bin/env python3
"""Interact with one contained live-ISO guest; evidence is never a boot/pass claim.

Use a TTY-backed supervising session. Only public disposable test data may be
typed: screenshots can contain typed text, and the terminal may echo input.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import select
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
HELPERS = runpy.run_path(str(ROOT / 'scripts/boot-test.py'), run_name='desktop_test_helpers')
contained, QMP, exclusive_runner = (HELPERS[name] for name in ('contained', 'QMP', 'exclusive_runner'))
TOOLS = ROOT / '.work/builder/tools'
QKEYS = set('abcdefghijklmnopqrstuvwxyz0123456789') | {
    'shift', 'shift_r', 'ctrl', 'ctrl_r', 'alt', 'alt_r', 'meta_l', 'meta_r',
    'esc', 'ret', 'tab', 'spc', 'backspace', 'insert', 'delete', 'home', 'end',
    'pgup', 'pgdn', 'left', 'right', 'up', 'down', 'caps_lock',
    'minus', 'equal', 'bracket_left', 'bracket_right', 'backslash', 'semicolon',
    'apostrophe', 'grave_accent', 'comma', 'dot', 'slash',
} | {f'f{number}' for number in range(1, 13)}
PLAIN = dict(zip('`-=[]\\;\',./ ', ('grave_accent', 'minus', 'equal', 'bracket_left',
                                 'bracket_right', 'backslash', 'semicolon', 'apostrophe',
                                 'comma', 'dot', 'slash', 'spc')))
SHIFTED = dict(zip('~!@#$%^&*()_+{}|:"<>?', ('grave_accent', '1', '2', '3', '4', '5',
                                        '6', '7', '8', '9', '0', 'minus', 'equal',
                                        'bracket_left', 'bracket_right', 'backslash',
                                        'semicolon', 'apostrophe', 'comma', 'dot', 'slash')))
HELP = ('screenshot (or shot) | status | keys ctrl+alt+t | text public test text | '
        'click X Y [left|middle|right] | help | stop')


def strict_path(value):
    """Reject internal aliases as well as escapes before any path is written."""
    raw = Path(value)
    resolved = contained(raw)
    if resolved != Path(os.path.abspath(raw)) or raw.is_symlink():
        raise ValueError('Symlinked runtime paths are refused')
    return resolved


def fresh(value):
    path = strict_path(value)
    if path.exists() or path.is_symlink():
        raise ValueError('Refusing an existing output path: ' + str(path))
    return path


def write_new(path, value):
    with fresh(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def ppm_dimensions(path):
    """Validate QEMU's P6/8-bit screendump format, including its pixel count."""
    path = strict_path(path)
    if not path.is_file():
        raise ValueError('Missing QEMU screenshot')
    with path.open('rb') as stream:
        magic, dimensions, maximum = stream.readline(16), stream.readline(64), stream.readline(16)
        match = re.fullmatch(rb'([1-9][0-9]{0,4}) ([1-9][0-9]{0,4})\n', dimensions)
        if magic != b'P6\n' or maximum != b'255\n' or not match:
            raise ValueError('Unexpected QEMU PPM header')
        width, height = map(int, match.groups())
        if width < 2 or height < 2 or width > 8192 or height > 8192:
            raise ValueError('Screenshot dimensions outside supported bounds')
        if path.stat().st_size != stream.tell() + width * height * 3:
            raise ValueError('Incomplete QEMU PPM pixels')
    return width, height


def text_keys(text):
    if not 1 <= len(text) <= 256 or any(not 32 <= ord(char) <= 126 for char in text):
        raise ValueError('Text must contain 1–256 printable ASCII characters')
    result = []
    for char in text:
        if 'a' <= char <= 'z' or '0' <= char <= '9':
            result.append([char])
        elif 'A' <= char <= 'Z':
            result.append(['shift', char.lower()])
        elif char in PLAIN:
            result.append([PLAIN[char]])
        elif char in SHIFTED:
            result.append(['shift', SHIFTED[char]])
        else:
            raise ValueError('Character has no supported US keyboard mapping')
    return result


def chord_keys(text):
    keys = text.split('+')
    if not 1 <= len(keys) <= 8 or len(set(keys)) != len(keys) or any(key not in QKEYS for key in keys):
        raise ValueError('Use 1–8 distinct supported QEMU qcodes joined by +')
    return keys


def environment(output):
    env = os.environ.copy()
    for key, leaf in {'HOME': 'home', 'TMPDIR': 'tmp', 'XDG_CACHE_HOME': 'cache',
                      'XDG_CONFIG_HOME': 'config', 'XDG_DATA_HOME': 'data',
                      'XDG_STATE_HOME': 'state', 'XDG_RUNTIME_DIR': 'runtime'}.items():
        directory = fresh(output / leaf)
        directory.mkdir(mode=0o700)
        env[key] = str(directory)
    env.update(LD_LIBRARY_PATH=f'{TOOLS}/usr/lib/x86_64-linux-gnu:{TOOLS}/lib/x86_64-linux-gnu',
               QEMU_MODULE_DIR=str(TOOLS / 'usr/lib/x86_64-linux-gnu/qemu'),
               PYTHONDONTWRITEBYTECODE='1')
    return env


def stop_owned(process, qmp):
    """Stop only the Popen object created here, with bounded fallback waits."""
    if process is not None and process.poll() is None:
        try:
            qmp.command('quit')
            process.wait(timeout=5)
        except (OSError, TimeoutError, RuntimeError, subprocess.TimeoutExpired):
            if process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=5)


class SessionTimeout(Exception):
    pass


class BoundedQMP(QMP):
    """Keep helper response waits inside the guest session's wall deadline."""
    def __init__(self, prefix, events, deadline):
        super().__init__(prefix, events)
        self.deadline = deadline

    def receive(self, timeout):
        if self.deadline is not None:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise SessionTimeout()
            timeout = min(timeout, remaining)
        try:
            return super().receive(timeout)
        except TimeoutError:
            if self.deadline is not None and time.monotonic() >= self.deadline:
                raise SessionTimeout() from None
            raise


class DesktopSession:
    def __init__(self, qmp, process, output, result, deadline, command_log):
        self.qmp, self.process, self.output, self.result = qmp, process, output, result
        self.deadline = deadline
        self.command_log = command_log
        self.dimensions = None

    def audit(self, command, **fields):
        self.command_log.write(json.dumps({'unix': time.time(), 'command': command, **fields}) + '\n')
        self.command_log.flush()

    def check_time(self):
        if time.monotonic() >= self.deadline:
            raise SessionTimeout('Interactive session deadline reached')

    def screenshot(self):
        self.check_time()
        if shutil.disk_usage(self.output).free < 512 * 1024 ** 2:
            raise RuntimeError('Less than512MiB remains for retained capture evidence')
        path = fresh(self.output / f'screen-{len(self.result["captures"]):04d}.ppm')
        self.qmp.command('screendump', {'filename': str(path)})
        self.dimensions = ppm_dimensions(path)
        capture = {'path': str(path), 'width': self.dimensions[0], 'height': self.dimensions[1], 'unix': time.time()}
        self.result['captures'].append(capture)
        print(json.dumps({'screenshot': capture}), flush=True)
        return self.dimensions

    def key_chord(self, keys):
        self.check_time()
        # send-key automatically schedules release, avoiding stuck keys on a
        # controller exception. Allow more wall time than its fixed hold time.
        self.qmp.command('send-key', {'keys': [{'type': 'qcode', 'data': key} for key in keys], 'hold-time': 30})
        time.sleep(0.10)

    def click(self, argument):
        words = argument.split()
        if len(words) not in (2, 3) or any(not re.fullmatch(r'[0-9]{1,5}', value) for value in words[:2]):
            raise ValueError('Use click X Y [left|middle|right] with nonnegative pixel coordinates')
        button = words[2] if len(words) == 3 else 'left'
        if button not in ('left', 'middle', 'right'):
            raise ValueError('Unsupported pointer button')
        previous = self.dimensions
        width, height = self.screenshot()
        if previous is None or previous != (width, height):
            raise ValueError('Display size changed; inspect the new screenshot before clicking')
        x, y = map(int, words[:2])
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError('Click coordinates are outside the captured framebuffer')
        self.qmp.command('input-send-event', {'events': [
            {'type': 'abs', 'data': {'axis': 'x', 'value': round(x * 32767 / (width - 1))}},
            {'type': 'abs', 'data': {'axis': 'y', 'value': round(y * 32767 / (height - 1))}},
        ]})
        try:
            self.qmp.command('input-send-event', {'events': [{'type': 'btn', 'data': {'down': True, 'button': button}}]})
            time.sleep(0.10)
        finally:
            self.qmp.command('input-send-event', {'events': [{'type': 'btn', 'data': {'down': False, 'button': button}}]})
        self.audit('click', x=x, y=y, button=button, width=width, height=height)

    def execute(self, line):
        self.check_time()
        command, separator, argument = line.partition(' ')
        if command in ('screenshot', 'shot', 'status', 'help', 'stop'):
            if separator:
                raise ValueError('This command takes no arguments')
            self.audit(command)
            if command in ('screenshot', 'shot'):
                self.screenshot()
            elif command == 'status':
                print(json.dumps({'status': self.qmp.command('query-status')}), flush=True)
            elif command == 'help':
                print(HELP, flush=True)
            return command != 'stop'
        if command == 'keys':
            keys = chord_keys(argument)
            self.audit('keys', key_count=len(keys), payload_redacted=True)
            self.key_chord(keys)
        elif command == 'text':
            chords = text_keys(argument)
            self.audit('text', length=len(argument), payload_redacted=True)
            for keys in chords:
                self.key_chord(keys)
        elif command == 'click':
            self.click(argument)
        else:
            raise ValueError('Unknown command; use help')
        return True

    def loop(self):
        self.screenshot()
        print(HELP + '\nPublic disposable test data only; no private authentication.', flush=True)
        pending = b''
        discarding = False
        while self.process.poll() is None:
            self.check_time()
            if not select.select([sys.stdin], [], [], min(1, max(0, self.deadline - time.monotonic())))[0]:
                continue
            chunk = os.read(sys.stdin.fileno(), 4096)
            if not chunk:
                return 'stdin-closed'
            pending += chunk
            while b'\n' in pending:
                raw, pending = pending.split(b'\n', 1)
                if discarding:
                    discarding = False
                    continue
                try:
                    if len(raw) > 1024:
                        raise ValueError('Command line exceeds1024bytes')
                    line = raw.removesuffix(b'\r').decode('ascii')
                    if line and not self.execute(line):
                        return 'operator-stopped'
                except (UnicodeError, ValueError) as error:
                    self.audit('rejected-input', error=str(error))
                    print(json.dumps({'input_error': str(error)}), flush=True)
            if len(pending) > 1024:
                pending = b''
                discarding = True
                self.audit('rejected-input', error='Command line exceeds1024bytes')
                print('Command line too long; discarded until next newline.', flush=True)
        return 'guest-exited'


def run(args):
    # Preflight all fixed paths before creating output or launching anything.
    iso, tools = strict_path(args.iso), strict_path(TOOLS)
    output = fresh(args.output or ROOT / 'artifacts' / f'desktop-test-{time.time_ns()}')
    if not iso.is_file() or iso.suffix.lower() != '.iso':
        raise ValueError('An existing regular project ISO is required')
    with iso.open('rb') as stream:
        stream.seek(32769)
        if stream.read(5) != b'CD001':
            raise ValueError('Input lacks the ISO9660 signature')
    qemu, firmware, datadir = (strict_path(tools / leaf) for leaf in
                              ('usr/bin/qemu-system-x86_64', 'usr/share/seabios/bios-256k.bin', 'usr/share/qemu'))
    if not qemu.is_file() or not firmware.is_file() or not datadir.is_dir():
        raise ValueError('Prepared project QEMU/SeaBIOS tools are missing')
    qimg = strict_path(tools / 'usr/bin/qemu-img')
    if args.disk_size and not qimg.is_file():
        raise ValueError('Prepared project qemu-img is missing')
    for leaf in ('home', 'tmp', 'cache', 'config', 'data', 'state', 'runtime', 'serial.log',
                 'qemu.log', 'qemu-debug.log', 'qmp.in', 'qmp.out', 'qmp-events.jsonl',
                 'commands.jsonl', 'run.json', 'result.json', 'disposable-install.qcow2', 'disk-create.log'):
        fresh(output / leaf)
    free = shutil.disk_usage(output.parent if output.parent.exists() else ROOT).free
    if free < (8 * 1024 ** 3 if args.disk_size else 1024 ** 3):
        raise ValueError('Insufficient free space for a retained desktop-test session')
    output.mkdir(parents=True, mode=0o700)
    try:
        return launch(args, iso, qemu, qimg, firmware, datadir, output)
    except BaseException as error:
        # Retain a result even if local setup fails before the QEMU try/finally.
        if not (output / 'result.json').exists():
            write_new(output / 'result.json', {'iso': str(iso), 'output': str(output),
                      'outcome': 'setup-failed', 'error': str(error), 'finished_unix': time.time(),
                      'boot_verified': False, 'login_verified': False,
                      'install_verified': False, 'workflows_verified': False})
        raise


def launch(args, iso, qemu, qimg, firmware, datadir, output):
    env = environment(output)
    disk = None
    if args.disk_size:
        disk = fresh(output / 'disposable-install.qcow2')
        with fresh(output / 'disk-create.log').open('x') as log:
            subprocess.run([str(qimg), 'create', '-f', 'qcow2', str(disk), args.disk_size],
                           env=env, cwd=output, check=True, stdout=log, stderr=subprocess.STDOUT)
    digest = hashlib.sha256()
    with iso.open('rb') as stream:
        for block in iter(lambda: stream.read(2 ** 20), b''):
            digest.update(block)
    serial = fresh(output / 'serial.log')
    command = [str(qemu), '-machine', 'pc,accel=tcg,smm=off', '-cpu', 'max', '-smp', '2',
               '-m', str(args.memory), '-bios', str(firmware), '-L', str(datadir),
               '-no-user-config', '-nodefaults', '-display', 'none', '-monitor', 'none', '-no-reboot',
               '-device', 'VGA', '-device', 'qemu-xhci,id=usb', '-device', 'usb-tablet,bus=usb.0',
               '-boot', 'order=d,menu=off', '-D', str(output / 'qemu-debug.log'), '-serial', 'file:' + str(serial),
               '-blockdev', json.dumps({'driver': 'file', 'filename': str(iso), 'node-name': 'iso-file', 'read-only': True}),
               '-blockdev', json.dumps({'driver': 'raw', 'file': 'iso-file', 'node-name': 'live-iso', 'read-only': True}),
               '-device', 'ide-cd,drive=live-iso,id=cdrom']
    if args.network == 'user':
        command += ['-netdev', 'user,id=net0', '-device', 'virtio-net-pci,netdev=net0,romfile=']
    else:
        command += ['-nic', 'none']
    if disk:
        command += ['-blockdev', json.dumps({'driver': 'file', 'filename': str(disk), 'node-name': 'disk-file'}),
                    '-blockdev', json.dumps({'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}),
                    '-device', 'virtio-blk-pci,drive=install-disk,serial=windows12-desktop-test']
    result = {'iso': str(iso), 'iso_sha256': digest.hexdigest(), 'output': str(output),
              'disposable_disk': str(disk) if disk else None, 'network': args.network,
              'started_unix': time.time(), 'captures': [], 'boot_verified': False,
              'login_verified': False, 'install_verified': False, 'workflows_verified': False,
              'outcome': 'starting', 'timeout_seconds': args.timeout}
    process = qmp = None
    exit_code = 1
    with fresh(output / 'qmp-events.jsonl').open('x') as events, fresh(output / 'commands.jsonl').open('x') as commands, fresh(output / 'qemu.log').open('x') as log:
        try:
            deadline = time.monotonic() + args.timeout
            qmp = BoundedQMP(strict_path(output / 'qmp'), events, deadline)
            command += ['-qmp', 'pipe:' + str(qmp.prefix)]
            process = subprocess.Popen(command, env=env, cwd=output, stdout=log, stderr=subprocess.STDOUT)
            write_new(output / 'run.json', {**result, 'command': command, 'pid': process.pid})
            print(json.dumps({'output': str(output), 'pid': process.pid}), flush=True)
            qmp.handshake()
            session = DesktopSession(qmp, process, output, result, deadline, commands)
            result['outcome'] = session.loop()
            exit_code = 0 if process.poll() in (None, 0) else 1
        except SessionTimeout:
            result['outcome'] = 'timed-out-not-certified'
            exit_code = 124
        except KeyboardInterrupt:
            result['outcome'] = 'interrupted'
            exit_code = 130
        except Exception as error:
            result.update(outcome='failed', error=str(error))
            print(json.dumps({'error': str(error)}), file=sys.stderr, flush=True)
        finally:
            if qmp is not None:
                qmp.deadline = None  # Cleanup has its own bounded waits.
                try:
                    stop_owned(process, qmp)
                except Exception as error:
                    result['cleanup_error'] = str(error)
                    exit_code = 1
                finally:
                    try:
                        qmp.close()
                    except OSError as error:
                        result['qmp_close_error'] = str(error)
            if process is not None:
                result['qemu_returncode'] = process.poll()
            result['finished_unix'] = time.time()
            write_new(output / 'result.json', result)
    print('Desktop session ended; boot/login/install/workflow verification requires separate reviewed evidence.', flush=True)
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--output', type=Path, help='New project-contained directory; never reused')
    parser.add_argument('--timeout', type=int, default=1800, help='1–7200seconds, default1800')
    parser.add_argument('--memory', type=int, default=4096, help='1024–8192MiB')
    parser.add_argument('--disk-size', help='Optional NEW disposable qcow2, 8G–128G; no existing disk accepted')
    parser.add_argument('--network', choices=('none', 'user'), default='none', help='No networking, or optional user NAT without forwards/shares')
    args = parser.parse_args()
    if not 1 <= args.timeout <= 7200 or not 1024 <= args.memory <= 8192:
        parser.error('timeout or memory outside supported bounds')
    if args.disk_size and (not re.fullmatch(r'[1-9][0-9]{0,2}G', args.disk_size) or not 8 <= int(args.disk_size[:-1]) <= 128):
        parser.error('disk size must be8G through128G')
    if not sys.stdin.isatty():
        parser.error('A TTY-backed session is required for bounded interactive control')
    with exclusive_runner():
        return run(args)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
