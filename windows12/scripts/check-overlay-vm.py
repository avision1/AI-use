#!/usr/bin/env python3
"""Check current overlay source in a disposable VM; optionally probe its proxy."""
import atexit
import argparse
import errno
import fcntl
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import ssl
import stat
import subprocess
import tarfile
import threading
import time

ROOT = Path(__file__).absolute().parent.parent
BUILDER = ROOT / '.work/builder'
MAX_SOURCE = 32 * 1024 * 1024
MAX_LOG = 4 * 1024 * 1024


def identity(info):
    # Reading may legitimately update atime; input identity excludes it.
    return tuple(getattr(info, field) for field in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))


def path(value, missing=False):
    value = Path(value)
    if not value.is_absolute() or '..' in value.parts or not value.is_relative_to(ROOT):
        raise ValueError('Project-contained absolute path required')
    for component in reversed((value, *value.parents)):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if missing:
                continue
            raise
        if stat.S_ISLNK(info.st_mode):
            raise ValueError('Symlink refused: ' + str(component))
        if component != value and not stat.S_ISDIR(info.st_mode):
            raise ValueError('Non-directory ancestor refused')
    return value


def read(value, maximum):
    value = path(value)
    with value.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > maximum:
            raise ValueError('Bounded single-link file required: ' + str(value))
        data = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    if len(data) > maximum or identity(before) != identity(after) or identity(value.stat()) != identity(after):
        raise ValueError('Input changed during read')
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(value, data):
    value = path(value, missing=True)
    with value.open('xb') as stream:
        stream.write(data)


def stopped_builder():
    # The shared runner lock excludes modern runners; refuse even a legacy
    # listener without sending control commands or changing old FIFO paths.
    inputs = [BUILDER / 'qmp.in', BUILDER / 'qmp.out']
    if not any(p.exists() for p in inputs):
        return
    for p in inputs:
        path(p)
        if not stat.S_ISFIFO(p.stat().st_mode):
            raise ValueError('Ambiguous old QMP control')
    fd = None
    try:
        fd = os.open(inputs[0], os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    except OSError as error:
        if error.errno != errno.ENXIO:
            raise
    else:
        raise ValueError('Existing QMP listener; reconcile previous VM first')
    finally:
        if fd is not None:
            os.close(fd)


def snapshot():
    output = io.BytesIO()
    files = {}
    total = 0
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for tree in ('image', 'tests', 'scripts', 'build'):
            base = path(ROOT / tree)
            for entry in sorted(base.rglob('*')):
                path(entry)
                if entry.is_dir():
                    continue
                data = read(entry, 1024 * 1024)
                total += len(data)
                if total > MAX_SOURCE:
                    raise ValueError('Current source exceeds 32 MiB')
                name = entry.relative_to(ROOT).as_posix()
                files[name] = sha(data)
                member = tarfile.TarInfo(name)
                member.mode = 0o755 if entry.stat().st_mode & 0o111 else 0o644
                member.size = len(data)
                member.mtime = 0
                archive.addfile(member, io.BytesIO(data))
    data = output.getvalue()
    if len(data) > MAX_SOURCE:
        raise ValueError('Source archive exceeds 32 MiB')
    return data, files


GUEST = r'''import hashlib,http.client,io,json,os,pathlib,shutil,ssl,subprocess,tarfile,traceback,urllib.request
origin=ORIGIN
expected=EXPECTED
nonce=NONCE
proxy_probe=PROXY_PROBE
root=pathlib.Path('/root/windows12-checks')
report={'schema':1,'nonce':nonce,'source_sha256':expected,'passed':False,'iso_verified':False}
log=bytearray()
def run(argv):
 p=subprocess.run(argv,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
 log.extend(p.stdout)
 if len(log)>4194304:raise ValueError('Guest check output exceeds 4 MiB')
 if p.returncode:raise ValueError('Guest command failed: '+repr(argv)+' rc='+str(p.returncode))
 return p.stdout
def upload(name,data):
 c=http.client.HTTPConnection('10.0.2.2',PORT,timeout=60)
 c.request('PUT','/output/'+name,data,{'Content-Length':str(len(data))})
 r=c.getresponse()
 if r.status!=201:raise ValueError('Export failed '+str(r.status))
 r.read();c.close()
try:
 assert os.geteuid()==0 and pathlib.Path('/run/windows12-build-vm').is_file()
 report['route_cleanup']={}
 for family in ('-4','-6'):
  prefix='0.0.0.0/0' if family=='-4' else '::/0'
  query=['ip','-j',family,'route','show','table','all','exact',prefix]
  routes=subprocess.run(query,capture_output=True,check=True,timeout=10)
  before=json.loads(routes.stdout)
  report['route_cleanup'][family]={'before':before}
  # Unreachable/blackhole/prohibit defaults cannot forward packets. IPv6
  # may expose an immutable unreachable default; never flush that kernel row.
  forwarding=[r for r in before if r.get('type','unicast') not in ('unreachable','blackhole','prohibit')]
  for route in forwarding:
   if route.get('type','unicast')!='unicast' or route.get('nexthops'):raise ValueError('Unsupported forwarding default route: '+repr(route))
   command=['ip',family,'route','del','default']
   if route.get('gateway'):command+=['via',route['gateway']]
   if route.get('dev'):command+=['dev',route['dev']]
   if 'metric' in route:command+=['metric',str(route['metric'])]
   if 'table' in route:command+=['table',str(route['table'])]
   subprocess.run(command,capture_output=True,check=True,timeout=10)
  routes=subprocess.run(query,capture_output=True,check=True,timeout=10)
  after=json.loads(routes.stdout)
  report['route_cleanup'][family]['after']=after
  if any(r.get('type','unicast') not in ('unreachable','blackhole','prohibit') for r in after):raise ValueError('Guest forwarding default route remains: '+routes.stdout.decode()[:2048])
 report['guest_forwarding_defaults_absent']=True
 raw=urllib.request.urlopen(origin+'/source.tar',timeout=60).read(33554433)
 if len(raw)>33554432 or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Source digest/length differs')
 root.mkdir(mode=0o700)
 with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(root,filter='data')
 if proxy_probe['enabled']:
  context=ssl.create_default_context()
  context.load_verify_locations(cadata=proxy_probe['certificate'])
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args,**kwargs):raise ValueError('Metadata redirects are refused')
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':proxy_probe['url']}),urllib.request.HTTPSHandler(context=context),NoRedirect())
  url='https://deb.debian.org/debian/dists/trixie/InRelease'
  with opener.open(url,timeout=60) as response:
   if response.status!=200 or response.geturl()!=url:raise ValueError('Unexpected metadata response or redirect')
   metadata=response.read(524289)
  if not 0<len(metadata)<=524288:raise ValueError('Metadata probe exceeds bound')
  probe_dir=root/'.work/proxy-probe';probe_dir.mkdir(parents=True)
  release=probe_dir/'InRelease';release.write_bytes(metadata)
  verifier=shutil.which('gpgv') or shutil.which('sqv')
  if not verifier:raise ValueError('Guest signature verifier unavailable')
  keyring='/usr/share/keyrings/debian-archive-keyring.gpg'
  if pathlib.Path(verifier).name=='gpgv':run([verifier,'--homedir',str(probe_dir),'--keyring',keyring,str(release)])
  else:run([verifier,'--keyring',keyring,'--output',str(probe_dir/'Release.verified'),'--cleartext',str(release)])
  report['proxy_probe']={'https_verified':True,'signature_verified':True,'url':url,'metadata_sha256':hashlib.sha256(metadata).hexdigest(),'certificate_sha256':proxy_probe['certificate_sha256']}
 run(['python3','-B','-m','unittest','discover','-s','tests','-v'])
 report['unit_tests_passed']=True
 run(['python3','-B','scripts/package-desktop.py'])
 package=list((root/'artifacts/packages').glob('*.deb'))
 if len(package)!=1:raise ValueError('Expected one desktop package')
 first=package[0].read_bytes()
 run(['python3','-B','scripts/package-desktop.py'])
 second=package[0].read_bytes()
 if first!=second:raise ValueError('Desktop package not deterministic')
 report.update(package_name=package[0].name,package_sha256=hashlib.sha256(first).hexdigest(),package_bytes=len(first),deterministic_package=True)
 run(['dpkg-deb','--info',str(package[0])])
 run(['dpkg-deb','--contents',str(package[0])])
 report.update(dpkg_inspection_passed=True,passed=True)
except BaseException as error:
 report['error']=str(error)[:2048]
 log.extend(traceback.format_exc().encode()[:8192])
finally:
 report['log_sha256']=hashlib.sha256(bytes(log)).hexdigest()
 upload('checks.log',bytes(log)[:4194304])
 upload('result.json',json.dumps(report,sort_keys=True).encode())
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--probe-proxy', action='store_true', help='Explicitly fetch bounded signed Debian metadata through the inherited proxy; no package installation')
    args = parser.parse_args()
    if not 60 <= args.timeout <= 1800:
        parser.error('--timeout must be 60..1800 seconds')
    path(ROOT)
    # Shared metadata only: never replace builder disk, source, FIFO or markers.
    lockpath = path(BUILDER / 'runner.lock')
    lock = lockpath.open('ab')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stopped_builder()
    config = json.loads(read(ROOT / 'build/builder-image.lock.json', 8192))
    name = config['filename']
    if Path(name).name != name or not re.fullmatch(r'[0-9a-f]{128}', config['sha512']):
        raise ValueError('Invalid cached cloud image lock')
    legacy = BUILDER / config.get('legacy_cache_name', name)
    cloud = path(legacy if legacy.is_file() else BUILDER / name)
    manifest = read(BUILDER / 'pinned-SHA512SUMS', 1024 * 1024)
    if sha(manifest) != config['manifest_sha256']:
        raise ValueError('Pinned cached manifest differs')
    if not any(line.split() == [config['sha512'], name] for line in manifest.decode().splitlines()):
        raise ValueError('Cloud image not bound to cached manifest')
    digest = hashlib.sha512()
    with cloud.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError('Regular cached cloud image required')
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
        after = os.fstat(stream.fileno())
    if identity(before) != identity(after) or identity(cloud.stat()) != identity(after) or digest.hexdigest() != config['sha512']:
        raise ValueError('Cached cloud image identity/SHA512 mismatch')
    source, files = snapshot()
    nonce = secrets.token_hex(16)
    out = path(ROOT / 'artifacts' / ('overlay-check-' + nonce), missing=True)
    out.mkdir(mode=0o700)
    for directory in ('home', 'tmp', 'cache', 'config', 'data'):
        (out / directory).mkdir(mode=0o700)
    write(out / 'source.tar', source)
    env = os.environ.copy()
    for key, directory in [('HOME','home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data')]:
        env[key] = str(out / directory)
    tools = path(BUILDER / 'tools')
    lib = tools / 'usr/lib/x86_64-linux-gnu'
    env.update(LD_LIBRARY_PATH=str(lib)+':'+str(tools/'lib/x86_64-linux-gnu'),QEMU_MODULE_DIR=str(lib/'qemu'),PYTHONDONTWRITEBYTECODE='1')
    qemu = path(tools/'usr/bin/qemu-system-x86_64')
    qimg = path(tools/'usr/bin/qemu-img')
    proxy_transport = None
    proxy_helper_hash = None
    proxy_probe = {'enabled': False}
    if args.probe_proxy:
        helper = path(ROOT/'scripts/guest-proxy.py')
        helper_bytes = read(helper,1024*1024)
        proxy_helper_hash = sha(helper_bytes)
        namespace = {'__file__':str(helper), '__name__':'overlay_guest_proxy'}
        exec(compile(helper_bytes,str(helper),'exec'),namespace)
        proxy_transport = namespace['GuestProxy'](env.get('HTTPS_PROXY',env.get('https_proxy','')))
        certificate_path = env.get('CODEX_PROXY_CERT')
        if not certificate_path:
            raise ValueError('Explicit proxy probe requires the configured public CODEX_PROXY_CERT')
        with Path(certificate_path).open('rb') as certificate_file:
            certificate_bytes = certificate_file.read(1024*1024+1)
        if len(certificate_bytes)>1024*1024:raise ValueError('Proxy certificate exceeds bound')
        certificate = certificate_bytes.decode('ascii')
        ssl.create_default_context().load_verify_locations(cadata=certificate)
        atexit.register(proxy_transport.close)
        proxy_transport.__enter__()
        if not proxy_transport.guest_url:raise ValueError('Explicit proxy probe requires a configured proxy')
        proxy_probe = {'enabled':True,'url':proxy_transport.guest_url,'certificate':certificate,'certificate_sha256':sha(certificate_bytes)}
    disk = out / 'check.qcow2'
    subprocess.run([str(qimg),'create','-f','qcow2','-F','qcow2','-b',str(cloud),str(disk),'4G'],env=env,check=True,timeout=30)
    received = set()
    seed = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *arguments):
            pass

        def do_GET(self):
            data = source if self.path == '/source.tar' else seed.get(self.path)
            if data is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name = self.path.removeprefix('/output/')
            maximum = {'checks.log':MAX_LOG,'result.json':16384}.get(name)
            if self.path != '/output/'+name or maximum is None or name in received:
                self.send_error(403)
                return
            try:
                length = int(self.headers['Content-Length'])
                if not 0 <= length <= maximum:
                    raise ValueError('Invalid export length')
                self.connection.settimeout(30)
                data = self.rfile.read(length)
                if len(data) != length:
                    raise ValueError('Truncated export')
                write(out / name,data)
                received.add(name)
            except (OSError,ValueError,TypeError,KeyError):
                self.send_error(400)
                return
            self.send_response(201)
            self.send_header('Content-Length','0')
            self.end_headers()

    server = http.server.HTTPServer(('127.0.0.1',0),Handler)
    port = server.server_port
    origin = 'http://10.0.2.2:'+str(port)
    guest = GUEST.replace('ORIGIN',repr(origin)).replace('EXPECTED',repr(sha(source))).replace('NONCE',repr(nonce)).replace('PORT',str(port)).replace('PROXY_PROBE',repr(proxy_probe))
    shell = "#!/bin/sh\ntrap 'sync; poweroff -f' EXIT\npython3 -B /root/check.py\n"
    data = '#cloud-config\nwrite_files:\n'
    for target, content in [('/run/windows12-build-vm','overlay-check\n'),('/root/check.py',guest),('/root/check.sh',shell)]:
        data += '  - path: '+target+'\n    permissions: "0700"\n    content: |\n'+''.join('      '+line+'\n' for line in content.splitlines())
    data += 'runcmd:\n  - [ /bin/sh, /root/check.sh ]\n'
    seed.update({'/seed/user-data':data.encode(),'/seed/meta-data':('instance-id: overlay-'+nonce+'\nlocal-hostname: overlay-check\n').encode(),'/seed/vendor-data':b'',
                 '/seed/network-config':b'version: 2\nethernets:\n  check:\n    match:\n      name: "en*"\n    addresses: [10.0.2.15/24]\n    dhcp4: false\n    dhcp6: false\n'})
    command = [str(qemu),'-machine','pc,accel=tcg,smm=off','-cpu','max','-smp','2','-m','2048','-bios',str(path(tools/'usr/share/seabios/bios-256k.bin')),
               '-L',str(path(tools/'usr/share/qemu')),'-no-user-config','-nodefaults','-display','none','-monitor','none','-no-reboot',
               '-serial','stdio','-drive','file='+str(disk)+',if=virtio,format=qcow2','-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0,romfile=',
               '-smbios','type=1,serial=ds=nocloud-net;s='+origin+'/seed/']
    record = {'schema':1,'nonce':nonce,'source_sha256':sha(source),'files':files,'cloud_sha512':config['sha512'],'command':command,'wrapper_sha256':sha(read(Path(__file__).absolute(),1024*1024)),'network':'static on-link guest config; guest removes and verifies absence of IPv4/IPv6 forwarding default routes before checks; initial cloud-init networking not independently isolated; no package download commands','started':time.time()}
    write(out/'run.json',json.dumps(record,indent=2).encode())
    write(out/'proxy-probe.json',json.dumps({'enabled':args.probe_proxy,'transport':proxy_transport.provenance if proxy_transport else None,'helper_sha256':proxy_helper_hash}).encode())
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    child = None
    error = None
    try:
        with (out/'serial.log').open('xb') as log:
            child = subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                code = child.wait(timeout=args.timeout)
                if code:
                    raise ValueError('Owned QEMU failed with '+str(code))
            except BaseException:
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        child.kill();child.wait()
                raise
        result = json.loads(read(out/'result.json',16384))
        if (result.get('schema')!=1 or result.get('nonce')!=nonce or result.get('source_sha256')!=sha(source)
                or result.get('passed') is not True or result.get('iso_verified') is not False
                or any(result.get(flag) is not True for flag in ('unit_tests_passed','deterministic_package','dpkg_inspection_passed','guest_forwarding_defaults_absent'))
                or not isinstance(result.get('package_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',result['package_sha256'])
                or type(result.get('package_bytes')) is not int or not 0<result['package_bytes']<=16*1024*1024
                or result.get('log_sha256')!=sha(read(out/'checks.log',MAX_LOG))):
            raise ValueError('Fresh guest proof failed; inspect output')
        if identity(cloud.stat())!=identity(after):
            raise ValueError('Cached backing image identity changed during check')
        if args.probe_proxy:
            proof = result.get('proxy_probe',{})
            if (any(proof.get(flag) is not True for flag in ('https_verified','signature_verified'))
                    or proof.get('url')!='https://deb.debian.org/debian/dists/trixie/InRelease'
                    or proof.get('certificate_sha256')!=proxy_probe['certificate_sha256']
                    or not isinstance(proof.get('metadata_sha256'),str)
                    or not re.fullmatch(r'[0-9a-f]{64}',proof['metadata_sha256'])):
                raise ValueError('Guest proxy HTTPS/signature proof missing or mismatched')
        print('Guest overlay tests and deterministic package checks passed:',out)
    except BaseException as exception:
        error = str(exception)
        raise
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        if proxy_transport is not None:proxy_transport.close()
        write(out/'host-result.json',json.dumps({'schema':1,'nonce':nonce,'error':error,'finished':time.time(),'qemu_stopped':child is None or child.poll() is not None}).encode())
        lock.close()


if __name__ == '__main__':
    try:
        main()
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        raise SystemExit('Overlay VM check failed: '+str(error))
