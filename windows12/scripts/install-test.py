#!/usr/bin/env python3
"""Install a live ISO to a NEW contained disk, then prove an ISO-free disk boot.
This is destructive only to the newly created disposable VM disk. Never use a
host block device, an existing disk, or this public test preseed on a real PC.
"""
import argparse
import contextlib
import errno
import fcntl
import hashlib
import http.server
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import runpy
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
HELPERS = runpy.run_path(str(ROOT / 'scripts/boot-test.py'), run_name='install_test_helpers')
contained, QMP = HELPERS['contained'], HELPERS['QMP']
TOOLS = ROOT / '.work/builder/tools'
ISO_TOOLS = ROOT / '.work/builder/iso-tools'


def environment(output, toolroot):
    env = os.environ.copy()
    for key, leaf in {'HOME': 'home', 'TMPDIR': 'tmp', 'XDG_CACHE_HOME': 'cache',
                      'XDG_CONFIG_HOME': 'config', 'XDG_DATA_HOME': 'data',
                      'XDG_STATE_HOME': 'state', 'XDG_RUNTIME_DIR': 'runtime'}.items():
        directory = contained(output / leaf)
        directory.mkdir(mode=0o700, exist_ok=True)
        env[key] = str(directory)
    env.update(LD_LIBRARY_PATH=f'{toolroot}/usr/lib/x86_64-linux-gnu:{toolroot}/lib/x86_64-linux-gnu',
               QEMU_MODULE_DIR=str(TOOLS / 'usr/lib/x86_64-linux-gnu/qemu'),
               PYTHONDONTWRITEBYTECODE='1')
    return env


@contextlib.contextmanager
def exclusive_runner():
    """Share the builder lock; probe legacy FIFOs without consuming QMP data."""
    work = contained(ROOT / '.work/builder')
    raw_lock = work / 'runner.lock'
    if raw_lock.is_symlink():
        raise ValueError('Runner lock symlink refused')
    lock = contained(raw_lock)
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'r+') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError('Runner lock is not a regular file')
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another build/install runner holds runner.lock; wait for its recorded job')
        qmp_in, qmp_out = work / 'qmp.in', work / 'qmp.out'
        if qmp_in.exists() or qmp_out.exists() or qmp_in.is_symlink() or qmp_out.is_symlink():
            for path in (qmp_in, qmp_out):
                if path.is_symlink() or not path.exists() or not stat.S_ISFIFO(path.stat().st_mode):
                    raise ValueError('Ambiguous legacy builder QMP controls; inspect the recorded build job')
            try:
                writer = os.open(qmp_in, os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
            except OSError as error:
                if error.errno != errno.ENXIO:
                    raise
            else:
                os.close(writer)
                raise ValueError('Legacy source-build QMP listener is active; wait for the build VM to stop')
        # Hold until both install and ISO-free verification guests have stopped.
        yield


def verify_xorriso(binary, output):
    """Match extracted executable to the bootstrap's authenticated package lock."""
    lock = json.loads((ROOT / 'build/iso-tools-lock.json').read_text())
    entry = lock.get('xorriso')
    if not entry or not entry.get('SHA256'):
        raise ValueError('Authenticated xorriso package lock missing')
    archive = contained(ROOT / '.work/builder/debs' / Path(entry['Filename']).name)
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['SHA256'] or not data.startswith(b'!<arch>\n'):
        raise ValueError('Cached xorriso package differs from bootstrap lock')
    decompressor = shutil.which('dpkg-deb')
    if not decompressor:
        raise ValueError('Read-only dpkg-deb decompression utility unavailable')
    env = environment(output, ISO_TOOLS)
    # Use the host utility's normal read-only runtime libraries; all writable
    # directories remain project-local. No package installation or extraction.
    env.pop('LD_LIBRARY_PATH', None)
    env.pop('QEMU_MODULE_DIR', None)
    payload = subprocess.run([decompressor, '--fsys-tarfile', str(archive)], env=env, cwd=output,
                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as stream:
        member = next((m for m in stream.getmembers()
                       if m.name.lstrip('./') == 'usr/bin/xorriso' and m.isfile()), None)
        if member and stream.extractfile(member).read() == binary.read_bytes():
            return
    raise ValueError('Extracted xorriso binary does not match its locked package')


def installer_files(iso, output, directory=None):
    binary = contained(ISO_TOOLS / 'usr/bin/xorriso')
    if not binary.is_file():
        raise ValueError('Run scripts/build-tools.py --profile iso before installation testing')
    verify_xorriso(binary, output)
    env = environment(output, ISO_TOOLS)
    with (output / 'xorriso.log').open('w') as log:
        listing = subprocess.run([str(binary), '-indev', str(iso), '-find', '/', '-type', 'f', '-exec', 'echo', '--'],
                                 env=env, cwd=output, check=True, stdout=subprocess.PIPE, stderr=log, text=True).stdout
        (output / 'iso-tree-files.txt').write_text(listing)
        files = set()
        for line in listing.splitlines():
            words = shlex.split(line)
            if len(words) == 1 and words[0].startswith('/'):
                path = PurePosixPath(words[0])
                if '..' in path.parts:
                    raise ValueError('Unexpected traversal in ISO path')
                files.add(str(path))
        candidates = {str(PurePosixPath(path).parent) for path in files
                      if PurePosixPath(path).name == 'vmlinuz'
                      and str(PurePosixPath(path).parent / 'initrd.gz') in files
                      and not path.startswith('/live/')}
        if directory:
            selected = str(PurePosixPath(directory))
            if selected not in candidates:
                raise ValueError('Requested installer directory lacks a discovered vmlinuz/initrd.gz pair')
        else:
            if not candidates:
                raise ValueError('No D-I vmlinuz/initrd.gz pair discovered; inspect iso-tree-files.txt')
            shortest = min(len(PurePosixPath(path).parts) for path in candidates)
            shallowest = sorted(path for path in candidates if len(PurePosixPath(path).parts) == shortest)
            if len(shallowest) != 1:
                raise ValueError('Ambiguous installer paths; select --installer-directory from iso-tree-files.txt')
            selected = shallowest[0]
        extracted = []
        for name in ('vmlinuz', 'initrd.gz'):
            destination = contained(output / ('installer-' + name))
            source = str(PurePosixPath(selected) / name)
            subprocess.run([str(binary), '-osirrox', 'on', '-indev', str(iso), '-extract', source, str(destination)],
                           env=env, cwd=output, check=True, stdout=log, stderr=subprocess.STDOUT)
            if not destination.is_file() or destination.stat().st_size < 1024:
                raise ValueError('Installer extraction missing/truncated')
            extracted.append(destination)
    return extracted, selected


def stop(process, qmp):
    if process.poll() is None:
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


def run_vm(name, common, extra, output, env, timeout, interval):
    """Return actual emulator status; caller separately evaluates guest proof."""
    serial = contained(output / f'{name}-serial.log')
    captures = []
    with (output / f'{name}-qmp.jsonl').open('w') as events, (output / f'{name}-qemu.log').open('w') as log:
        qmp = QMP(contained(output / f'{name}-qmp'), events)
        command = common + ['-D', str(output / f'{name}-debug.log'), '-serial', 'file:' + str(serial),
                            '-qmp', 'pipe:' + str(qmp.prefix)] + extra
        process = None
        timed_out = False
        try:
            process = subprocess.Popen(command, env=env, cwd=output, stdout=log, stderr=subprocess.STDOUT)
            (output / f'{name}-run.json').write_text(json.dumps({'pid': process.pid, 'command': command}, indent=2) + '\n')
            qmp.handshake()
            deadline = time.monotonic() + timeout
            next_capture = 0
            while process.poll() is None:
                now = time.monotonic()
                if now >= deadline:
                    timed_out = True
                    break
                if now >= next_capture:
                    try:
                        status = qmp.command('query-status')
                        image = contained(output / f'{name}-screen-{len(captures):04d}.ppm')
                        qmp.command('screendump', {'filename': str(image)})
                        captures.append({'path': str(image), 'status': status, 'unix': time.time()})
                    except (OSError, TimeoutError, RuntimeError):
                        if process.poll() is None:
                            raise
                    next_capture = time.monotonic() + interval
                time.sleep(1)
        finally:
            if process is not None:
                stop(process, qmp)
            qmp.close()
    return {'returncode': process.returncode, 'timed_out': timed_out, 'captures': captures, 'serial': str(serial)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('iso', type=Path)
    parser.add_argument('--output', type=Path, help='NEW project-contained output directory')
    parser.add_argument('--disk-size', default='24G', help='NEW disposable disk capacity, default 24G')
    parser.add_argument('--installer-directory', help='Select a discovered ISO directory if discovery is ambiguous')
    parser.add_argument('--install-timeout', type=int, default=3600)
    parser.add_argument('--boot-timeout', type=int, default=600)
    parser.add_argument('--interval', type=int, default=60)
    args = parser.parse_args()
    if not re.fullmatch(r'[1-9][0-9]*G', args.disk_size) or min(args.install_timeout, args.boot_timeout, args.interval) < 1:
        parser.error('Positive timeouts/interval and disk size such as 24G required')
    iso = contained(args.iso)
    if not iso.is_file() or iso.suffix.lower() != '.iso':
        raise ValueError('Existing project-contained .iso required')
    with iso.open('rb') as stream:
        stream.seek(32769)
        if stream.read(5) != b'CD001':
            raise ValueError('Input is not an ISO9660 image')
    output = contained(args.output or ROOT / 'artifacts' / f'install-test-{time.time_ns()}')
    if output.exists():
        raise ValueError('Refusing existing output directory; no disk/output reuse supported')
    for path in (TOOLS / 'usr/bin/qemu-system-x86_64', TOOLS / 'usr/bin/qemu-img', TOOLS / 'usr/share/seabios/bios-256k.bin'):
        if not contained(path).is_file():
            raise ValueError('Project QEMU/SeaBIOS tools missing')
    with exclusive_runner():
        nearest = output.parent
        while not nearest.exists():
            nearest = nearest.parent
        free = shutil.disk_usage(nearest).free
        required = max(8 * 2 ** 30, 3 * iso.stat().st_size)
        if free < required:
            raise ValueError(f'Insufficient free storage: {free / 2**30:.1f} GiB available, '
                             f'{required / 2**30:.1f} GiB required by test heuristic. '
                             'Preserve source/logs and deliberately reclaim reproducible build state; '
                             'this harness never removes builder storage.')
        return execute(args, iso, output)


def execute(args, iso, output):
    output.mkdir(parents=True, mode=0o700)
    env = environment(output, TOOLS)
    result = {'iso': str(iso), 'output': str(output), 'install_verified': False, 'disk_boot_verified': False,
              'gui_verified': False, 'started_unix': time.time(), 'outcome': 'starting'}
    server = None
    try:
        (kernel, initrd), directory = installer_files(iso, output, args.installer_directory)
        result['installer_directory'] = directory
        digest = hashlib.sha256()
        with iso.open('rb') as stream:
            for block in iter(lambda: stream.read(2 ** 20), b''):
                digest.update(block)
        result['iso_sha256'] = digest.hexdigest()
        disk = contained(output / 'disposable-install.qcow2')
        if disk.exists():
            raise ValueError('Refusing existing disk')
        with (output / 'disk-create.log').open('w') as log:
            subprocess.run([str(TOOLS / 'usr/bin/qemu-img'), 'create', '-f', 'qcow2', str(disk), args.disk_size],
                           env=env, cwd=output, stdout=log, stderr=subprocess.STDOUT, check=True)
        token = secrets.token_hex(12)
        serial_id = 'W12' + token
        marker = 'WINDOWS12_INSTALLED_BOOT_OK:' + token
        complete = threading.Event()
        served = {}
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/complete-' + token:
                    (output / 'completion-callback.json').write_text(json.dumps({'unix': time.time(), 'path': self.path}) + '\n')
                    complete.set()
                    body = b'completion recorded\n'
                elif self.path in served:
                    body = served[self.path]
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *unused):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        endpoint = 'http://10.0.2.2:' + str(server.server_port)
        # Fail closed before partitioning: exactly one disk, its expected serial,
        # and the fixed virtio name. A guard failure powers off the VM.
        guard = f'test "$(ls /sys/block | grep -E \'^(sd|vd|hd|nvme|xvd)\')" = vda && test "$(cat /sys/block/vda/serial)" = {serial_id}'
        late = '''#!/bin/sh
set -eu
GUARD
[ -f /target/etc/debian_version ]
in-target dpkg-query -W -f='${db:Status-Status}' windows12-desktop | grep -qx installed
mkdir -p /target/usr/local/sbin /target/etc/systemd/system/multi-user.target.wants
cat > /target/usr/local/sbin/windows12-install-proof <<'PROOF'
#!/bin/sh
set -eu
[ -f /etc/debian_version ]
root=$(findmnt -n -o SOURCE /)
case "$root" in /dev/vda[0-9]*) ;; *) exit 1;; esac
[ "$(dpkg-query -W -f='${db:Status-Status}' windows12-desktop)" = installed ]
getent passwd testuser >/dev/null
python3 - <<'CONFIG_AUDIT'
import json
from pathlib import Path
import re
import subprocess

# Known transient trust artifacts must be absent, including broken symlinks.
for root in ('/usr/local/share/ca-certificates', '/usr/share/ca-certificates', '/etc/ssl/certs'):
    directory = Path(root)
    for filename in ('windows12-build-proxy.crt', 'windows12-build-proxy.pem'):
        for candidate in directory.rglob(filename) if directory.is_dir() else ():
            if candidate.exists() or candidate.is_symlink():
                raise SystemExit('Transient build CA leaked: ' + str(candidate))
apt = Path('/etc/apt')
files = list(apt.rglob('*')) if apt.is_dir() else []
files.append(Path('/etc/environment'))
for filename in files:
    if not filename.is_file():
        continue
    for line in filename.read_text(errors='replace').splitlines():
        stripped = line.strip()
        if stripped.startswith(('#', '//')):
            continue
        if 'proxy' in line.lower() and re.search(r'(?<![0-9.])10[.]0[.]2[.]2(?![0-9.])', line):
            raise SystemExit('Transient build proxy configuration leaked: ' + str(filename))

def systemctl(*arguments):
    return subprocess.check_output(['systemctl', *arguments], text=True, timeout=20).strip()

default_target = systemctl('get-default')
fragment = systemctl('show', '--property=FragmentPath', '--value', 'display-manager.service')
manager_file = Path('/etc/X11/default-display-manager')
manager = manager_file.read_text().strip() if manager_file.is_file() else None
if default_target != 'graphical.target' or Path(fragment).name != 'sddm.service':
    raise SystemExit('Expected graphical.target and configured SDDM display-manager service')
if manager is not None and Path(manager).name != 'sddm':
    raise SystemExit('Unexpected default-display-manager configuration')
audit = {'default_target': default_target, 'display_manager_unit': Path(fragment).name,
         'display_manager_file': manager, 'build_proxy_ca_absent': True,
         'build_proxy_entries_absent': True, 'gui_runtime_verified': False}
with Path('/dev/ttyS0').open('a') as console:
    console.write('CONFIG_MARKER ' + json.dumps(audit, sort_keys=True) + chr(10))
CONFIG_AUDIT
printf '\\nMARKER root=%s package=%s\\n' "$root" "$(dpkg-query -W -f='${Version}' windows12-desktop)" >/dev/ttyS0
sync
systemctl --no-block poweroff
PROOF
chmod 755 /target/usr/local/sbin/windows12-install-proof
cat > /target/etc/systemd/system/windows12-install-proof.service <<'SERVICE'
[Unit]
Description=Disposable Windows12 installed-root boot proof
After=local-fs.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/windows12-install-proof
[Install]
WantedBy=multi-user.target
SERVICE
ln -s ../windows12-install-proof.service /target/etc/systemd/system/multi-user.target.wants/windows12-install-proof.service
wget -O /dev/null ENDPOINT/complete-TOKEN
'''.replace('GUARD', '(' + guard + ') || exit 71').replace('CONFIG_MARKER', 'WINDOWS12_INSTALLED_CONFIG:' + token).replace('MARKER', marker).replace('ENDPOINT', endpoint).replace('TOKEN', token)
        preseed = f'''# PUBLIC disposable test credentials. Never use on a physical PC.
d-i debian-installer/locale string en_US.UTF-8
d-i keyboard-configuration/xkb-keymap select us
d-i netcfg/choose_interface select auto
d-i netcfg/get_hostname string windows12-install-test
d-i netcfg/get_domain string invalid
d-i hw-detect/load_firmware boolean false
d-i choose-mirror/skip boolean true
d-i mirror/country string manual
d-i mirror/http/hostname string invalid.example
d-i mirror/http/directory string /debian
d-i mirror/http/proxy string
d-i apt-setup/use_mirror boolean false
d-i apt-setup/services-select multiselect
d-i clock-setup/utc boolean true
d-i time/zone string Etc/UTC
d-i clock-setup/ntp boolean false
d-i passwd/root-login boolean false
d-i passwd/make-user boolean true
d-i passwd/user-fullname string Windows12 Test
d-i passwd/username string testuser
d-i passwd/user-password password testpass
d-i passwd/user-password-again password testpass
d-i user-setup/allow-password-weak boolean true
d-i user-setup/encrypt-home boolean false
d-i partman/early_command string ({guard}) || {{ echo WRONG_DISK_GUARD >/dev/ttyS0; poweroff -f; sleep 999999; }}
d-i partman-auto/disk string /dev/vda
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select atomic
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true
d-i live-installer/enable boolean true
d-i pkgsel/upgrade select none
tasksel tasksel/first multiselect
popularity-contest popularity-contest/participate boolean false
d-i grub-installer/only_debian boolean true
d-i grub-installer/bootdev string /dev/vda
d-i cdrom-detect/eject boolean false
d-i finish-install/reboot_in_progress note
d-i debian-installer/exit/poweroff boolean true
d-i preseed/late_command string wget -O /tmp/windows12-late.sh {endpoint}/late-{token}.sh && sh /tmp/windows12-late.sh
'''
        (output / 'preseed.cfg').write_text(preseed)
        (output / 'late-install.sh').write_text(late)
        served['/preseed-' + token + '.cfg'] = preseed.encode()
        served['/late-' + token + '.sh'] = late.encode()
        common = [str(TOOLS / 'usr/bin/qemu-system-x86_64'), '-machine', 'pc,accel=tcg,smm=off',
                  '-cpu', 'max', '-smp', '2', '-m', '4096', '-bios', str(TOOLS / 'usr/share/seabios/bios-256k.bin'),
                  '-L', str(TOOLS / 'usr/share/qemu'), '-no-user-config', '-nodefaults', '-no-reboot',
                  '-display', 'none', '-monitor', 'none', '-device', 'VGA',
                  '-blockdev', json.dumps({'driver': 'file', 'filename': str(disk), 'node-name': 'disk-file'}),
                  '-blockdev', json.dumps({'driver': 'qcow2', 'file': 'disk-file', 'node-name': 'install-disk'}),
                  '-device', 'virtio-blk-pci,drive=install-disk,serial=' + serial_id]
        install = ['-kernel', str(kernel), '-initrd', str(initrd), '-append',
                   'auto=true priority=critical interface=auto console=ttyS0,115200n8 preseed/url=' + endpoint + '/preseed-' + token + '.cfg',
                   '-netdev', 'user,id=net0', '-device', 'virtio-net-pci,netdev=net0,romfile=',
                   '-blockdev', json.dumps({'driver': 'file', 'filename': str(iso), 'read-only': True, 'node-name': 'iso-file'}),
                   '-blockdev', json.dumps({'driver': 'raw', 'file': 'iso-file', 'read-only': True, 'node-name': 'live-iso'}),
                   '-device', 'ide-cd,drive=live-iso,id=cdrom']
        result['disk'] = str(disk)
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        result['install_run'] = run_vm('install', common, install, output, env, args.install_timeout, args.interval)
        result['completion_callback'] = complete.is_set()
        if result['install_run']['timed_out'] or result['install_run']['returncode'] != 0 or not complete.is_set():
            raise RuntimeError('Installer completion not established; inspect install-serial.log and captures')
        server.shutdown()
        server.server_close()
        server = None
        # NO ISO, direct kernel, host share or network on the verification boot.
        result['boot_run'] = run_vm('installed-boot', common, ['-boot', 'order=c', '-nic', 'none'],
                                    output, env, args.boot_timeout, args.interval)
        serial = (output / 'installed-boot-serial.log').read_text(errors='replace')
        proof = re.search(re.escape(marker) + r' root=/dev/vda[0-9]+ package=([^\s]+)', serial)
        config_proof = re.search(re.escape('WINDOWS12_INSTALLED_CONFIG:' + token) + r' (\{[^\r\n]+\})', serial)
        if result['boot_run']['timed_out'] or result['boot_run']['returncode'] != 0 or not proof or not config_proof:
            raise RuntimeError('ISO-free installed boot/configuration proof missing; no installation success certified')
        audit = json.loads(config_proof.group(1))
        if (audit.get('default_target') != 'graphical.target' or audit.get('display_manager_unit') != 'sddm.service'
                or audit.get('build_proxy_ca_absent') is not True or audit.get('build_proxy_entries_absent') is not True):
            raise RuntimeError('Installed configuration audit did not pass')
        result.update(install_verified=True, disk_boot_verified=True, configuration_audit=audit,
                      installed_package_version=proof.group(1), outcome='installed-root-boot-proof-passed')
        return 0
    except KeyboardInterrupt:
        result['outcome'] = 'interrupted'
        return 130
    except Exception as error:
        result.update(outcome='failed', error=str(error))
        print(str(error), file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        result['finished_unix'] = time.time()
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print('Evidence:', output, '; inspect result.json; GUI remains unverified.')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
