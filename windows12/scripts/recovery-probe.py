#!/usr/bin/env python3
"""Bounded, independent full-VM cloud-init reboot/rerun probe.
Each phase is a separate invocation so transient infrastructure proxy values refresh.
Never touches the production builder disk, QMP controls, or HTTP server.
"""
import argparse
import fcntl
import hashlib
import http.server
import json
import os
from pathlib import Path
import select
import subprocess
import threading
import time
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work/recovery-probe'
OUT = ROOT / 'artifacts/recovery-probe'
TOOLS = ROOT / '.work/builder/tools'
PORT = 8767
PROGRAM = '''import hashlib,http.client,json,os
from pathlib import Path
counter=Path('/root/windows12-recovery-count')
count=int(counter.read_text())+1 if counter.exists() else 1
counter.write_text(str(count))
report={'phase':int(os.environ['RECOVERY_PHASE']),'count':count,'token':os.environ['RECOVERY_ENV_TOKEN'],'proxy':os.environ.get('http_proxy',''),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
connection=http.client.HTTPConnection('10.0.2.2',8767,timeout=30)
connection.request('POST','/callback',json.dumps(report),{'Content-Type':'application/json'})
response=connection.getresponse()
if response.status!=201:raise RuntimeError('Callback failed '+str(response.status))
response.read();connection.close()
'''


def contained(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise SystemExit('Path escapes project: ' + str(path))
    if any(char in str(path) for char in (',', '\n', '\r', '\x00')):
        raise SystemExit('Unsupported runtime path separator')
    return path


class QMP:
    def __init__(self, prefix):
        self.buffer = b''
        self.sequence = 0
        for suffix in ('.in', '.out'):
            path = Path(str(prefix) + suffix)
            if path.exists() or path.is_symlink():
                raise SystemExit('Existing QMP path; reconcile previous job: ' + str(path))
            os.mkfifo(path, 0o600)
        self.reader = os.open(str(prefix) + '.out', os.O_RDWR | os.O_NONBLOCK)
        self.writer = os.open(str(prefix) + '.in', os.O_RDWR | os.O_NONBLOCK)

    def message(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            if b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                if line.strip():
                    return json.loads(line)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('QMP timeout')
            if select.select([self.reader], [], [], remaining)[0]:
                self.buffer += os.read(self.reader, 65536)

    def command(self, execute):
        self.sequence += 1
        os.write(self.writer, (json.dumps({'execute': execute, 'id': self.sequence}) + '\n').encode())
        deadline = time.monotonic() + 15
        while True:
            reply = self.message(max(0, deadline - time.monotonic()))
            if reply.get('id') == self.sequence:
                if 'error' in reply:
                    raise RuntimeError(str(reply['error']))
                return reply.get('return')

    def close(self):
        os.close(self.reader)
        os.close(self.writer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=int, choices=(1, 2), required=True)
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if not 30 <= args.timeout <= 600:
        parser.error('timeout must be 30..600 seconds')
    for path in (WORK, OUT):
        if path.is_symlink():
            raise SystemExit('Owned probe root symlink refused: ' + str(path))
        contained(path).mkdir(parents=True, exist_ok=True)
    lockpath = WORK / 'runner.lock'
    if lockpath.is_symlink():
        raise SystemExit('Runner lock symlink refused')
    lock = lockpath.open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    phaseout = contained(OUT / ('phase-' + str(args.phase)))
    if phaseout.exists():
        raise SystemExit('Phase output already exists; preserve it and do not overwrite')
    phaseout.mkdir(mode=0o700)
    env = os.environ.copy()
    for variable, leaf in {'HOME':'home','TMPDIR':'tmp','XDG_CACHE_HOME':'cache','XDG_CONFIG_HOME':'config','XDG_DATA_HOME':'data','XDG_STATE_HOME':'state','XDG_RUNTIME_DIR':'runtime'}.items():
        directory = contained(WORK / leaf)
        directory.mkdir(mode=0o700, exist_ok=True)
        env[variable] = str(directory)
    lib = contained(TOOLS / 'usr/lib/x86_64-linux-gnu')
    env.update(LD_LIBRARY_PATH=str(lib)+':'+str(TOOLS/'lib/x86_64-linux-gnu'), QEMU_MODULE_DIR=str(lib/'qemu'), PYTHONDONTWRITEBYTECODE='1')
    qemu = contained(TOOLS / 'usr/bin/qemu-system-x86_64')
    qimg = contained(TOOLS / 'usr/bin/qemu-img')
    firmware = contained(TOOLS / 'usr/share/seabios/bios-256k.bin')
    image_lock = json.loads((ROOT / 'build/builder-image.lock.json').read_text())
    builder = contained(ROOT / '.work/builder')
    legacy_name = image_lock.get('legacy_cache_name', image_lock['filename'])
    if any(Path(name).name != name for name in (legacy_name, image_lock['filename'])):
        raise SystemExit('Invalid builder cache filename')
    legacy = builder / legacy_name
    cloud = contained(legacy if legacy.is_file() else builder / image_lock['filename'])
    if not cloud.is_relative_to(builder):
        raise SystemExit('Builder image cache escapes its owned builder directory')
    expected = image_lock['sha512']
    digest = hashlib.sha512()
    with cloud.open('rb') as source:
        for block in iter(lambda: source.read(2**20), b''):
            digest.update(block)
    if digest.hexdigest() != expected:
        raise SystemExit('Cloud image digest mismatch')
    raw_disk = WORK / 'probe.qcow2'
    if raw_disk.is_symlink():
        raise SystemExit('Probe disk symlink refused')
    disk = contained(raw_disk)
    if not disk.is_relative_to(WORK.resolve()):
        raise SystemExit('Probe disk escapes owned recovery work directory')
    source_sha = hashlib.sha256(PROGRAM.encode()).hexdigest()
    statepath = contained(WORK / 'source-state.json')
    if args.phase == 1:
        if disk.exists() or statepath.exists():
            raise SystemExit('Probe state already exists; never overwrite an existing disk')
        subprocess.run([str(qimg),'create','-f','qcow2','-F','qcow2','-b',str(cloud),str(disk),'4G'], env=env, cwd=WORK, check=True)
        statepath.write_text(json.dumps({'source_sha256':source_sha,'base_sha512':expected})+'\n')
    else:
        if not disk.is_file() or not statepath.is_file():
            raise SystemExit('Phase 1 preserved disk/source state missing')
        if json.loads(statepath.read_text())['source_sha256'] != source_sha:
            raise SystemExit('Frozen probe source changed; refusing mixed-source rerun')
        first = json.loads((OUT/'phase-1/result.json').read_text())
        if not first.get('verified'):
            raise SystemExit('Phase 1 was not verified')
    proxy = urllib.parse.urlsplit(os.environ.get('HTTPS_PROXY',os.environ.get('https_proxy','')))
    translated = 'http://10.0.2.2:' + str(proxy.port) if proxy.hostname in ('127.0.0.1','localhost') and proxy.port else ''
    token = 'phase-' + str(args.phase) + '-' + str(time.time_ns())
    runner = ['env','RECOVERY_PHASE='+str(args.phase),'RECOVERY_ENV_TOKEN='+token,'http_proxy='+translated,'no_proxy=10.0.2.2,127.0.0.1,localhost','python3','/root/windows12-recovery-probe.py']
    userdata = '#cloud-config\nwrite_files:\n  - path: /root/windows12-recovery-probe.py\n    permissions: "0700"\n    content: |\n' + ''.join('      '+line+'\n' for line in PROGRAM.splitlines())
    userdata += 'runcmd:\n  - ' + json.dumps(runner) + '\n  - [ shutdown, -h, now ]\n'
    seed = {'/seed/meta-data':('instance-id: windows12-recovery-'+token+'\nlocal-hostname: windows12-recovery\n').encode(),'/seed/user-data':userdata.encode(),'/seed/vendor-data':b'', '/seed/network-config':b'version: 2\nethernets:\n  probe:\n    match:\n      name: "en*"\n    dhcp4: true\n    dhcp6: false\n'}
    report = {}
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in seed:
                self.send_error(404);return
            payload=seed[self.path]
            self.send_response(200);self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
        def do_POST(self):
            if self.path!='/callback':self.send_error(403);return
            try:
                length=int(self.headers['Content-Length'])
                if not 0 < length <= 8192:raise ValueError('length')
                data=json.loads(self.rfile.read(length))
                if data.get('phase')!=args.phase or data.get('token')!=token or data.get('source_sha256')!=source_sha:raise ValueError('phase/source/token mismatch')
            except (ValueError,TypeError,KeyError):self.send_error(400);return
            report.update(data)
            (phaseout/'callback.json').write_text(json.dumps(data,indent=2)+'\n')
            self.send_response(201);self.send_header('Content-Length','0');self.end_headers()
        def log_message(self,format,*values):
            with (phaseout/'http-requests.log').open('a') as log:log.write(json.dumps({'request':self.requestline,'values':values,'unix':time.time()})+'\n')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    prefix=contained(phaseout/'qmp')
    control=QMP(prefix)
    command=[str(qemu),'-machine','pc,accel=tcg,smm=off','-cpu','max','-smp','1','-m','1024','-bios',str(firmware),'-L',str(TOOLS/'usr/share/qemu'),'-no-user-config','-nodefaults','-display','none','-monitor','none','-no-reboot','-qmp','pipe:'+str(prefix),'-serial','stdio','-drive',f'file={disk},if=virtio,format=qcow2','-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0,romfile=','-smbios',f'type=1,serial=ds=nocloud-net;s=http://10.0.2.2:{PORT}/seed/']
    result={'phase':args.phase,'source_sha256':source_sha,'proxy':translated,'token':token,'command':command,'verified':False,'started_unix':time.time()}
    process=None
    try:
        with (phaseout/'serial.log').open('w') as serial:
            process=subprocess.Popen(command,env=env,cwd=WORK,stdout=serial,stderr=subprocess.STDOUT)
            result['pid']=process.pid
            (phaseout/'run.json').write_text(json.dumps(result,indent=2)+'\n')
            greeting=control.message(45)
            if 'QMP' not in greeting:raise RuntimeError('Missing QMP greeting')
            control.command('qmp_capabilities')
            deadline=time.monotonic()+args.timeout
            while process.poll() is None and time.monotonic()<deadline:
                time.sleep(1)
            if process.poll() is None:raise TimeoutError('VM did not finish within bounded timeout')
            result['qemu_returncode']=process.returncode
            result['callback']=report
            result['verified']=process.returncode==0 and report.get('count')==args.phase and report.get('proxy')==translated
            if not result['verified']:raise RuntimeError('Callback/count/proxy evidence did not verify phase')
    except Exception as error:
        result['error']=str(error)
    finally:
        if process is not None and process.poll() is None:
            try:control.command('quit');process.wait(timeout=5)
            except Exception:
                process.terminate()
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        result['finished_unix']=time.time()
        (phaseout/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        control.close();server.shutdown();server.server_close()
    print(json.dumps({'phase':args.phase,'verified':result['verified'],'output':str(phaseout),'error':result.get('error')},indent=2))
    return 0 if result['verified'] else 1


if __name__=='__main__':
    raise SystemExit(main())
