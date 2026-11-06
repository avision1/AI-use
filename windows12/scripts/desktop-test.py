#!/usr/bin/env python3
"""Interact with one contained live or installed guest; captures never certify it.

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
import stat
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
HELPERS = runpy.run_path(str(ROOT / 'scripts/boot-test.py'), run_name='desktop_test_helpers')
contained, QMP, exclusive_runner = (HELPERS[name] for name in ('contained', 'QMP', 'exclusive_runner'))
TOOLS = ROOT / '.work/builder/tools'
CPU_PROFILES = ('max', 'Nehalem')
VIDEO_PROFILES = {
    'standard': ('VGA', 'vgabios-stdvga.bin'),
    'virtio': ('virtio-vga', 'vgabios-virtio.bin'),
}
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


def identity(info):
    return tuple(getattr(info, field) for field in
                 ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns'))


def checked_open(value):
    path = strict_path(value)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    stream = os.fdopen(descriptor, 'rb')
    info = os.fstat(stream.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size <= 0:
        stream.close()
        raise ValueError('Evidence must be a nonempty single-link regular file: ' + str(path))
    return path, stream, info


def unchanged_file(path, stream, before):
    if identity(before) != identity(os.fstat(stream.fileno())) or identity(before) != identity(strict_path(path).lstat()):
        raise ValueError('Evidence changed while reading: ' + str(path))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate evidence JSON key: ' + key)
        result[key] = value
    return result


def read_evidence(value, json_record=True):
    path, stream, before = checked_open(value)
    with stream:
        if before.st_size > 8 * 1024 ** 2:
            raise ValueError('Evidence exceeds the 8MiB bound')
        payload = stream.read(8 * 1024 ** 2 + 1)
        unchanged_file(path, stream, before)
    text = payload.decode('utf-8')
    record = json.loads(text, object_pairs_hook=unique_object) if json_record else text
    if json_record and not isinstance(record, dict):
        raise ValueError('Evidence JSON must be an object')
    return record, {'path': str(path), 'sha256': hashlib.sha256(payload).hexdigest()}


def file_snapshot(value, kind):
    """Hash a stopped regular file without updating it; reject indirect images."""
    path, stream, before = checked_open(value)
    with stream:
        head = stream.read(65536)
        if kind == 'iso' and (path.suffix.lower() != '.iso' or head[32769:32774] != b'CD001'):
            raise ValueError('Prior ISO lacks the ISO9660 signature')
        if kind == 'qcow2':
            version = int.from_bytes(head[4:8], 'big')
            if (head[:4] != b'QFI\xfb' or version not in (2, 3) or len(head) < (104 if version == 3 else 72)
                    or int.from_bytes(head[8:20], 'big') != 0
                    or int.from_bytes(head[24:32], 'big') == 0
                    or (version == 3 and int.from_bytes(head[72:80], 'big') != 0)):
                raise ValueError('Baseline must be a clean standalone qcow2 without backing/external data')
        digest = hashlib.sha256(head)
        for block in iter(lambda: stream.read(2 ** 20), b''):
            digest.update(block)
        unchanged_file(path, stream, before)
    return {'path': str(path), 'sha256': digest.hexdigest(), 'bytes': before.st_size,
            'device': before.st_dev, 'inode': before.st_ino, 'mtime_ns': before.st_mtime_ns,
            'ctime_ns': before.st_ctime_ns, 'mode': before.st_mode, 'links': before.st_nlink}


def stopped_run(record):
    pid, command = record.get('pid'), record.get('command')
    if type(pid) is not int or pid <= 0 or not isinstance(command, list) or not command or any(type(arg) is not str for arg in command):
        raise ValueError('Prior run lacks unambiguous PID/command provenance')
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError('Prior run PID is active; refuse baseline use')
    nodes = []
    for index, arg in enumerate(command):
        if arg == '-blockdev':
            if index + 1 >= len(command):
                raise ValueError('Incomplete prior block device command')
            nodes.append(json.loads(command[index + 1], object_pairs_hook=unique_object))
    if any(not isinstance(node, dict) for node in nodes):
        raise ValueError('Invalid prior block graph')
    return command, nodes


def installed_source(value):
    """Validate all prior proof/provenance before creating any output or child."""
    result_path = strict_path(value)
    report, report_provenance = read_evidence(result_path)
    prior = result_path.parent
    if result_path.name != 'result.json' or report.get('output') != str(prior):
        raise ValueError('Installed result must belong to its recorded output directory')
    required = ('install_verified', 'disk_boot_verified', 'proof_service_one_shot', 'proof_stamp_reported', 'completion_callback')
    if any(report.get(key) is not True for key in required) or report.get('outcome') != 'installed-root-boot-proof-passed':
        raise ValueError('Complete successful one-shot installed proof is required')
    disk = strict_path(prior / 'disposable-install.qcow2')
    if report.get('disk') != str(disk):
        raise ValueError('Baseline disk differs from prior output disk')
    if type(report.get('iso')) is not str:
        raise ValueError('Prior ISO path is missing or malformed')
    iso = strict_path(report['iso'])
    if report.get('iso') != str(iso):
        raise ValueError('Prior ISO must have an absolute canonical path')
    phase_provenance, commands, node_sets = {}, {}, {}
    for phase, key in (('install', 'install_run'), ('installed-boot', 'boot_run')):
        phase_result = report.get(key)
        if (not isinstance(phase_result, dict) or type(phase_result.get('returncode')) is not int
                or phase_result['returncode'] != 0 or phase_result.get('timed_out') is not False
                or phase_result.get('serial') != str(prior / (phase + '-serial.log'))):
            raise ValueError('Prior installation/boot phase did not finish cleanly')
        record, provenance = read_evidence(prior / (phase + '-run.json'))
        command, nodes = stopped_run(record)
        commands[phase], node_sets[phase], phase_provenance[phase] = command, nodes, provenance
    disk_nodes = [{'driver': 'file', 'filename': str(disk), 'node-name': 'disk-file'},
                  {'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}]
    iso_nodes = [{'driver': 'file', 'filename': str(iso), 'read-only': True, 'node-name': 'iso-file'},
                 {'driver': 'raw', 'file': 'iso-file', 'read-only': True, 'node-name': 'live-iso'}]
    if node_sets['install'] != disk_nodes + iso_nodes or node_sets['installed-boot'] != disk_nodes:
        raise ValueError('Prior ISO/disk block provenance is incomplete or ambiguous')
    boot = commands['installed-boot']
    if (any(arg in boot for arg in ('-kernel', '-initrd', '-append', '-cdrom', '-drive', '-hda', '-hdb', '-hdd', '-fda', '-pflash'))
            or boot.count('-boot') != 1 or boot[boot.index('-boot') + 1:boot.index('-boot') + 2] != ['order=c']
            or boot.count('-nic') != 1 or boot[boot.index('-nic') + 1:boot.index('-nic') + 2] != ['none']
            or '-netdev' in boot):
        raise ValueError('Prior installed boot was not ISO-free and network-free')
    serial, serial_provenance = read_evidence(prior / 'installed-boot-serial.log', False)
    proofs = re.findall(r'WINDOWS12_INSTALLED_BOOT_OK:([0-9a-f]{24}) root=/dev/vda[0-9]+ package=([^\s]+) proof_once=([0-9a-f]{24})(?:\r?\n|$)', serial)
    configurations = re.findall(r'WINDOWS12_INSTALLED_CONFIG:([0-9a-f]{24}) (\{[^\r\n]+\})', serial)
    if (len(proofs) != 1 or len(configurations) != 1 or serial.count('WINDOWS12_INSTALLED_BOOT_OK:') != 1
            or serial.count('WINDOWS12_INSTALLED_CONFIG:') != 1):
        raise ValueError('Missing or ambiguous installed serial proof')
    token, version, stamp = proofs[0]
    audit = json.loads(configurations[0][1], object_pairs_hook=unique_object)
    if (token != stamp or configurations[0][0] != token or report.get('installed_package_version') != version
            or report.get('configuration_audit') != audit or not isinstance(audit, dict)
            or audit.get('default_target') != 'graphical.target' or audit.get('display_manager_unit') != 'sddm.service'
            or audit.get('build_proxy_ca_absent') is not True or audit.get('build_proxy_entries_absent') is not True):
        raise ValueError('Installed proof token, package or configuration disagrees')
    expected_device = 'virtio-blk-pci,drive=install-disk,serial=W12' + token[:17]
    if any(command.count(expected_device) != 1 for command in commands.values()):
        raise ValueError('Prior disk serial does not match installed proof token')
    iso_snapshot = file_snapshot(iso, 'iso')
    if iso_snapshot['sha256'] != report.get('iso_sha256'):
        raise ValueError('Prior ISO SHA256 no longer matches')
    baseline = file_snapshot(disk, 'qcow2')
    seal = report.get('installed_disk')
    if (not isinstance(seal, dict) or any(type(seal.get(key)) is not int for key in ('bytes', 'device', 'inode', 'mtime_ns'))
            or any(seal.get(key) != baseline[key] for key in ('path', 'sha256', 'bytes', 'device', 'inode', 'mtime_ns'))):
        raise ValueError('Installed disk seal no longer matches the stopped baseline')
    return {'result': report_provenance, 'runs': phase_provenance, 'serial': serial_provenance,
            'baseline': baseline, 'iso': str(iso), 'iso_sha256': iso_snapshot['sha256'],
            'proof_token': token, 'installed_package_version': version, 'configuration_audit': audit}


def disk_arguments(disk, source=None):
    """Use an explicit read-only standalone baseline graph in installed mode."""
    command = []
    if source:
        command += ['-blockdev', json.dumps({'driver': 'file', 'filename': source['baseline']['path'],
                                           'node-name': 'baseline-file', 'read-only': True}),
                    '-blockdev', json.dumps({'driver': 'qcow2', 'file': 'baseline-file', 'node-name': 'baseline',
                                            'read-only': True, 'backing': None})]
    node = {'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}
    if source:
        node['backing'] = 'baseline'
    return command + ['-blockdev', json.dumps({'driver': 'file', 'filename': str(disk), 'node-name': 'disk-file'}),
                      '-blockdev', json.dumps(node),
                      '-device', 'virtio-blk-pci,drive=install-disk,serial=windows12-desktop-test']


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
    _, (_, video_rom) = diagnostic_profiles(args)
    source = installed_source(args.installed_result) if args.installed_result else None
    iso, tools = strict_path(source['iso'] if source else args.iso), strict_path(TOOLS)
    output = fresh(args.output or ROOT / 'artifacts' / f'desktop-test-{time.time_ns()}')
    if not iso.is_file() or iso.suffix.lower() != '.iso':
        raise ValueError('An existing regular project ISO is required')
    with iso.open('rb') as stream:
        stream.seek(32769)
        if stream.read(5) != b'CD001':
            raise ValueError('Input lacks the ISO9660 signature')
    qemu, firmware, datadir = (strict_path(tools / leaf) for leaf in
                              ('usr/bin/qemu-system-x86_64', 'usr/share/seabios/bios-256k.bin', 'usr/share/qemu'))
    vgabios = strict_path(firmware.parent / video_rom)
    if not qemu.is_file() or not firmware.is_file() or not vgabios.is_file() or not datadir.is_dir():
        raise ValueError('Prepared project QEMU/SeaBIOS tools are missing')
    qimg = strict_path(tools / 'usr/bin/qemu-img')
    if (args.disk_size or source) and not qimg.is_file():
        raise ValueError('Prepared project qemu-img is missing')
    for leaf in ('home', 'tmp', 'cache', 'config', 'data', 'state', 'runtime', 'serial.log',
                 'qemu.log', 'qemu-debug.log', 'qmp.in', 'qmp.out', 'qmp-events.jsonl',
                 'commands.jsonl', 'run.json', 'result.json', 'disposable-install.qcow2',
                 'installed-desktop.qcow2', 'disk-create.log'):
        fresh(output / leaf)
    free = shutil.disk_usage(output.parent if output.parent.exists() else ROOT).free
    if free < (8 * 1024 ** 3 if args.disk_size or source else 1024 ** 3):
        raise ValueError('Insufficient free space for a retained desktop-test session')
    output.mkdir(parents=True, mode=0o700)
    try:
        return launch(args, iso, qemu, qimg, firmware, datadir, output, source)
    except BaseException as error:
        # Retain a result even if local setup fails before the QEMU try/finally.
        if not (output / 'result.json').exists():
            write_new(output / 'result.json', {'iso': str(iso), 'output': str(output),
                      'outcome': 'setup-failed', 'error': str(error), 'finished_unix': time.time(),
                      'mode': 'installed' if source else 'live', 'installed_source': source,
                      'disposable_disk': str(output / 'installed-desktop.qcow2') if source else None,
                      'boot_verified': False, 'login_verified': False,
                      'install_verified': False, 'workflows_verified': False})
        raise


def diagnostic_profiles(args):
    """Select only fixed contained emulation profiles; never accept QEMU fragments."""
    if args.cpu_profile not in CPU_PROFILES or args.video not in VIDEO_PROFILES:
        raise ValueError('Unsupported CPU or video diagnostic profile')
    return args.cpu_profile, VIDEO_PROFILES[args.video]


def desktop_command(args, iso, qemu, firmware, datadir, output, disk=None, source=None):
    serial = output / 'serial.log'
    cpu_profile, (video_device, video_rom) = diagnostic_profiles(args)
    command = [str(qemu), '-machine', 'pc,accel=tcg,smm=off', '-cpu', cpu_profile, '-smp', '2',
               '-m', str(args.memory), '-bios', str(firmware), '-L', str(datadir),
               '-no-user-config', '-nodefaults', '-display', 'none', '-monitor', 'none', '-no-reboot',
               '-device', video_device + ',romfile=' + str(Path(firmware).parent / video_rom),
               '-device', 'qemu-xhci,id=usb', '-device', 'usb-tablet,bus=usb.0',
               '-boot', 'order=c,menu=off' if source else 'order=d,menu=off',
               '-D', str(output / 'qemu-debug.log'), '-serial', 'file:' + str(serial)]
    if not source:
        command += ['-blockdev', json.dumps({'driver': 'file', 'filename': str(iso), 'node-name': 'iso-file', 'read-only': True}),
                    '-blockdev', json.dumps({'driver': 'raw', 'file': 'iso-file', 'node-name': 'live-iso', 'read-only': True}),
                    '-device', 'ide-cd,drive=live-iso,id=cdrom']
    if args.network == 'user':
        command += ['-netdev', 'user,id=net0', '-device', 'virtio-net-pci,netdev=net0,romfile=']
    else:
        command += ['-nic', 'none']
    if disk:
        command += disk_arguments(disk, source)
    return command


def baseline_unchanged(source):
    if file_snapshot(source['baseline']['path'], 'qcow2') != source['baseline']:
        raise ValueError('Installed baseline changed; retained child is not certified')


def launch(args, iso, qemu, qimg, firmware, datadir, output, source=None):
    env = environment(output)
    disk = None
    if source or args.disk_size:
        disk = fresh(output / ('installed-desktop.qcow2' if source else 'disposable-install.qcow2'))
        create = [str(qimg), 'create', '-f', 'qcow2']
        if source:
            baseline_unchanged(source)
            create += ['-F', 'qcow2', '-b', source['baseline']['path'], str(disk)]
        else:
            create += [str(disk), args.disk_size]
        with fresh(output / 'disk-create.log').open('x') as log:
            subprocess.run(create, env=env, cwd=output, check=True, stdout=log, stderr=subprocess.STDOUT)
    if source:
        digest = source['iso_sha256']
    else:
        hasher = hashlib.sha256()
        with iso.open('rb') as stream:
            for block in iter(lambda: stream.read(2 ** 20), b''):
                hasher.update(block)
        digest = hasher.hexdigest()
    fresh(output / 'serial.log')
    command = desktop_command(args, iso, qemu, firmware, datadir, output, disk, source)
    result = {'iso': str(iso), 'iso_sha256': digest, 'output': str(output),
              'mode': 'installed' if source else 'live', 'installed_source': source,
              'baseline_unchanged': False if source else None,
              'disposable_disk': str(disk) if disk else None, 'network': args.network,
              'cpu_profile': args.cpu_profile, 'video': args.video,
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
            if source:
                baseline_unchanged(source)
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
            if source:
                try:
                    baseline_unchanged(source)
                    result['baseline_unchanged'] = True
                except (OSError, ValueError) as error:
                    result['baseline_error'] = str(error)
                    result['outcome'] = 'baseline-changed-not-certified'
                    exit_code = 1
            result['finished_unix'] = time.time()
            write_new(output / 'result.json', result)
    print('Desktop session ended; boot/login/install/workflow verification requires separate reviewed evidence.', flush=True)
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path, nargs='?')
    parser.add_argument('--installed-result', type=Path, help='Successful sealed install-test result.json; boot a NEW child without ISO')
    parser.add_argument('--output', type=Path, help='New project-contained directory; never reused')
    parser.add_argument('--timeout', type=int, default=1800, help='1–7200seconds, default1800')
    parser.add_argument('--memory', type=int, default=4096, help='1024–8192MiB')
    parser.add_argument('--cpu-profile', choices=CPU_PROFILES, default='max', help='Contained TCG CPU diagnostic profile; default max')
    parser.add_argument('--video', choices=tuple(VIDEO_PROFILES), default='standard', help='Standard VGA or 2D virtio-vga; no host GPU access')
    parser.add_argument('--disk-size', help='Optional NEW disposable qcow2, 8G–128G; no existing disk accepted')
    parser.add_argument('--network', choices=('none', 'user'), default='none', help='No networking, or optional user NAT without forwards/shares')
    args = parser.parse_args()
    if bool(args.iso) == bool(args.installed_result):
        parser.error('Supply exactly one ISO or --installed-result')
    if args.installed_result and args.disk_size:
        parser.error('--disk-size is only supported for live ISO sessions')
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
