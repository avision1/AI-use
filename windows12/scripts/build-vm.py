#!/usr/bin/env python3
"""Build in a full TCG VM. No host mounts, chroot, package installs or block devices.
Writable guest storage: .work/builder/build.qcow2 and artifacts/vm-build ONLY.
"""
from pathlib import Path
import argparse, hashlib, http.server, json, os, shlex, shutil, subprocess, tarfile, threading, urllib.parse, time, socket, re
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.work/builder'
TOOLS=WORK/'tools'
OUT=ROOT/'artifacts/vm-build'

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--prepare',action='store_true',help='Download checksum-verified official builder image only')
 ap.add_argument('--probe',action='store_true',help='Run QEMU TCG firmware for 10s with no disk/network')
 ap.add_argument('--resume',action='store_true',help='Resume an existing VM disk, not a new build')
 args=ap.parse_args()
 for p in [WORK,OUT,WORK/'home',WORK/'tmp',WORK/'cache']:p.mkdir(parents=True,exist_ok=True)
 for p in [WORK,OUT,ROOT/'image']:
  if not p.resolve().is_relative_to(ROOT):raise SystemExit('Symlink escapes project: '+str(p))
 env=os.environ.copy()
 env.update(HOME=str(WORK/'home'),TMPDIR=str(WORK/'tmp'),XDG_CACHE_HOME=str(WORK/'cache'),PYTHONDONTWRITEBYTECODE='1')
 lib=TOOLS/'usr/lib/x86_64-linux-gnu'
 env['LD_LIBRARY_PATH']=str(lib)+':'+str(TOOLS/'lib/x86_64-linux-gnu')
 env['QEMU_MODULE_DIR']=str(lib/'qemu')
 def run(cmd,**kw):return subprocess.run(cmd,env=env,check=True,**kw)
 qemu=TOOLS/'usr/bin/qemu-system-x86_64';qimg=TOOLS/'usr/bin/qemu-img'
 if not qemu.exists():raise SystemExit('Run python3 scripts/build-tools.py first. No global installation is attempted.')
 firmware=TOOLS/'usr/share/seabios/bios-256k.bin'
 common=[str(qemu),'-machine','pc,accel=tcg,smm=off','-cpu','max','-smp','2','-m','4096','-bios',str(firmware),'-L',str(TOOLS/'usr/share/qemu'),'-no-user-config','-nodefaults','-display','none','-monitor','none','-no-reboot']
 if args.probe:
  try:run(common+['-serial','stdio','-net','none'],timeout=10)
  except subprocess.TimeoutExpired:print('QEMU TCG process remained running for 10s; no guest OS verified.')
  return
 # HTTPS checksum manifest pins exact builder bytes. Debian signatures are not verified here;
 # HTTPS origin authentication plus SHA512 detects transfer/cache corruption, not a compromised origin.
 base='https://cloud.debian.org/images/cloud/trixie/latest/'
 name='debian-13-genericcloud-amd64.qcow2'
 sums=WORK/'cloud-SHA512SUMS';cloud=WORK/name
 def download(url,path):
  if not path.exists():
   run(['curl','--fail','--location','--retry','2','--output',str(path)+'.part',url]);Path(str(path)+'.part').rename(path)
 download(base+'SHA512SUMS',sums)
 expected=next((line.split()[0] for line in sums.read_text().splitlines() if line.split()[-1]==name),None)
 if not expected:raise SystemExit('Expected builder image missing from upstream manifest')
 download(base+name,cloud)
 h=hashlib.sha512()
 with cloud.open('rb') as f:
  for block in iter(lambda:f.read(2**20),b''):h.update(block)
 if h.hexdigest()!=expected:raise SystemExit('Builder SHA512 mismatch; cached input left untouched for investigation.')
 (OUT/'input-provenance.json').write_text(json.dumps({'url':base+name,'sha512':expected,'verification':'official HTTPS SHA512SUMS; detached signature not verified','tools_lock':'build/tools-lock.json'},indent=2)+'\n')
 if args.prepare:return
 disk=WORK/'build.qcow2'
 if args.resume and not disk.exists():raise SystemExit('No VM disk to resume')
 if disk.exists() and not args.resume:raise SystemExit('Build disk exists. Use --resume or preserve then remove it deliberately. No automatic deletion.')
 if not disk.exists():
  run([str(qimg),'create','-f','qcow2','-F','qcow2','-b',str(cloud),str(disk),'20G'])
 # Resume uses the immutable archived source, not possibly changed working files.
 checks=WORK/'checks.tar'
 source_lock=WORK/'build-source.sha256'
 if args.resume:
  if not checks.exists() or not source_lock.exists():raise SystemExit('Resume requires preserved checks.tar and build-source.sha256')
  source_hash=hashlib.sha256(checks.read_bytes()).hexdigest()
  if source_lock.read_text().strip()!=source_hash:raise SystemExit('Archived source digest mismatch; refusing resume')
  print('Resuming frozen source snapshot',source_hash,flush=True)
 else:
  pending=WORK/'checks.pending.tar'
  with tarfile.open(pending,'w') as tf:
   for name in ['image','tests','scripts','build']:
    for p in sorted((ROOT/name).rglob('*')):
     if p.is_symlink():raise SystemExit('Source symlink requires review: '+str(p))
     if p.is_file():tf.add(p,arcname=p.relative_to(ROOT),recursive=False)
  source_hash=hashlib.sha256(pending.read_bytes()).hexdigest()
  pending.replace(checks);source_lock.write_text(source_hash+'\n')
 proxy=urllib.parse.urlsplit(env.get('HTTPS_PROXY',env.get('https_proxy','')))
 proxy_guest=''
 if proxy.hostname in ['127.0.0.1','localhost'] and proxy.port:
  proxy_guest=f'http://10.0.2.2:{proxy.port}'
 with tarfile.open(checks) as tf:guest=tf.extractfile('build/guest-build.sh').read().decode()
 user_data='#cloud-config\nwrite_files:\n  - path: /run/windows12-build-vm\n    content: "contained full VM build\\n"\n  - path: /root/build.sh\n    permissions: "0700"\n    content: |\n'+''.join('      '+line+'\n' for line in guest.splitlines())
 if proxy_guest:
  user_data+='  - path: /etc/apt/apt.conf.d/80windows12-build-proxy\n    content: |\n      Acquire::http::Proxy "'+proxy_guest+'";\n      Acquire::https::Proxy "'+proxy_guest+'";\n'
 runner=['bash','/root/build.sh']
 if proxy_guest:runner=['env','http_proxy='+proxy_guest,'https_proxy='+proxy_guest,'HTTP_PROXY='+proxy_guest,'HTTPS_PROXY='+proxy_guest,'no_proxy=10.0.2.2,127.0.0.1,localhost','NO_PROXY=10.0.2.2,127.0.0.1,localhost']+runner
 user_data+='runcmd:\n  - '+json.dumps(runner)+'\n'
 seed={'/seed/meta-data':b'instance-id: windows12-builder-INSTANCE\nlocal-hostname: windows12-builder\n','/seed/user-data':user_data.encode(),'/seed/vendor-data':b''}
 class Handler(http.server.BaseHTTPRequestHandler):
  def do_PUT(self):
   name=self.path.removeprefix('/output/')
   allowed={'build.exit','guest-build.log','desktop-SHA256SUMS','windows12-amd64-preview.iso','windows12-amd64-preview.packages','SHA256SUMS'}
   if not self.path.startswith('/output/') or (name not in allowed and not re.fullmatch(r'windows12-desktop_[A-Za-z0-9.+~_-]+_all\.deb',name)):
    self.send_error(403);return
   target=OUT/name;partial=OUT/(name+'.part')
   if target.is_symlink() or partial.is_symlink() or not target.resolve().is_relative_to(ROOT) or not partial.resolve().is_relative_to(ROOT):
    self.send_error(403);return
   try:length=int(self.headers['Content-Length'])
   except (TypeError,ValueError):self.send_error(411);return
   if length<0 or length>12*1024**3 or shutil.disk_usage(OUT).free<length+256*1024**2:
    self.send_error(413);return
   remaining=length
   with partial.open('wb') as destination:
    while remaining:
     block=self.rfile.read(min(1024*1024,remaining))
     if not block:self.send_error(400);return
     destination.write(block);remaining-=len(block)
   partial.replace(target)
   self.send_response(201);self.send_header('Content-Length','0');self.end_headers()
  def do_GET(self):
   if self.path=='/checks.tar':
    payload=checks
    self.send_response(200);self.send_header('Content-Length',str(payload.stat().st_size));self.end_headers()
    with payload.open('rb') as f:shutil.copyfileobj(f,self.wfile)
   elif self.path in seed:
    data=seed[self.path];self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   else:self.send_error(404)
  def log_message(self,*args):pass
 seed['/seed/meta-data']=seed['/seed/meta-data'].replace(b'INSTANCE',str(time.time_ns()).encode())
 old_status=OUT/'build.exit'
 if old_status.exists():old_status.rename(OUT/f'build.exit.previous-{time.time_ns()}')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),Handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 qmp=WORK/'qmp'
 for extension in ['.in','.out']:
  fifo=Path(str(qmp)+extension)
  if fifo.exists():fifo.unlink()
  os.mkfifo(fifo,0o600)
 cmd=common+['-qmp','pipe:'+str(qmp),'-serial','stdio','-drive',f'file={disk},if=virtio,format=qcow2','-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0,romfile=','-smbios','type=1,serial=ds=nocloud-net;s=http://10.0.2.2:8765/seed/']
 (OUT/'run.json').write_text(json.dumps({'command':cmd,'disk':str(disk),'output':str(OUT),'resume':args.resume,'source_sha256':source_hash},indent=2)+'\n')
 try:
  with (OUT/'serial.log').open('a') as log:run(cmd,stdout=log,stderr=subprocess.STDOUT)
 finally:server.shutdown()
 status=OUT/'build.exit'
 if not status.exists() or status.read_text().strip()!='0':raise SystemExit('Build incomplete/failed; inspect artifacts/vm-build/serial.log and guest-build.log')
 iso=OUT/'windows12-amd64-preview.iso'
 if not iso.is_file() or iso.stat().st_size==0:raise SystemExit('Guest reported success without nonempty ISO; refusing success.')
 expected_iso=(OUT/'SHA256SUMS').read_text().split()[0]
 actual_iso=hashlib.sha256()
 with iso.open('rb') as source:
  for block in iter(lambda:source.read(2**20),b''):actual_iso.update(block)
 if actual_iso.hexdigest()!=expected_iso:raise SystemExit('Exported ISO SHA256 mismatch')
 print('Built',iso,'; boot/install validation remains required.')
if __name__=='__main__':main()
