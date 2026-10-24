#!/usr/bin/env python3
"""Build in a full TCG VM. No host mounts, chroot, package installs or block devices.
Writable guest storage: .work/builder/build.qcow2 and artifacts/vm-build ONLY.
"""
from pathlib import Path
import argparse, hashlib, http.server, json, os, shlex, shutil, subprocess, tarfile, threading, urllib.parse, time
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
 common=[str(qemu),'-machine','pc,accel=tcg','-cpu','max','-smp','2','-m','4096','-bios',str(firmware),'-L',str(TOOLS/'usr/share/qemu'),'-no-user-config','-nodefaults','-display','none','-monitor','none','-no-reboot']
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
 if disk.exists() and not args.resume:raise SystemExit('Build disk exists. Use --resume or preserve then remove it deliberately. No automatic deletion.')
 if not disk.exists():
  run([str(qimg),'create','-f','qcow2','-F','qcow2','-b',str(cloud),str(disk),'20G'])
 # Source snapshot is read-only to VM through explicit HTTP map; no repo or arbitrary host share.
 archive=WORK/'source.tar'
 with tarfile.open(archive,'w') as tf:
  for p in sorted((ROOT/'image').rglob('*')):
   if p.is_symlink():raise SystemExit('Overlay symlink requires explicit review: '+str(p))
   if p.is_file():tf.add(p,arcname=p.relative_to(ROOT/'image'),recursive=False)
 checks=WORK/'checks.tar'
 with tarfile.open(checks,'w') as tf:
  for name in ['image','tests','scripts']:
   for p in sorted((ROOT/name).rglob('*')):
    if p.is_symlink():raise SystemExit('Source symlink requires review: '+str(p))
    if p.is_file():tf.add(p,arcname=p.relative_to(ROOT),recursive=False)
 proxy=urllib.parse.urlsplit(env.get('HTTPS_PROXY',env.get('https_proxy','')))
 proxy_guest=''
 if proxy.hostname in ['127.0.0.1','localhost'] and proxy.port:
  proxy_guest=f'http://10.0.2.2:{proxy.port}'
 guest=(ROOT/'build/guest-build.sh').read_text()
 user_data='#cloud-config\nwrite_files:\n  - path: /run/windows12-build-vm\n    content: "contained full VM build\\n"\n  - path: /root/build.sh\n    permissions: "0700"\n    content: |\n'+''.join('      '+line+'\n' for line in guest.splitlines())
 if proxy_guest:
  user_data+='  - path: /etc/apt/apt.conf.d/80windows12-build-proxy\n    content: |\n      Acquire::http::Proxy "'+proxy_guest+'";\n      Acquire::https::Proxy "'+proxy_guest+'";\n'
 user_data+='runcmd:\n  - [ bash, /root/build.sh ]\n'
 seed={'/seed/meta-data':b'instance-id: windows12-builder-INSTANCE\nlocal-hostname: windows12-builder\n','/seed/user-data':user_data.encode(),'/seed/vendor-data':b''}
 class Handler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   if self.path in ['/source.tar','/checks.tar']:
    payload=archive if self.path=='/source.tar' else checks
    self.send_response(200);self.send_header('Content-Length',str(payload.stat().st_size));self.end_headers()
    with payload.open('rb') as f:shutil.copyfileobj(f,self.wfile)
   elif self.path in seed:
    data=seed[self.path];self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   else:self.send_error(404)
  def log_message(self,*args):pass
 seed['/seed/meta-data']=seed['/seed/meta-data'].replace(b'INSTANCE',str(time.time_ns()).encode())
 source_hash=hashlib.sha256(checks.read_bytes()).hexdigest()
 source_lock=WORK/'build-source.sha256'
 if args.resume and source_lock.exists() and source_lock.read_text().strip()!=source_hash:raise SystemExit('Source changed since VM creation; preserve existing disk and start a new build.')
 source_lock.write_text(source_hash+'\n')
 old_status=OUT/'build.exit'
 if old_status.exists():old_status.rename(OUT/f'build.exit.previous-{time.time_ns()}')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),Handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 cmd=common+['-serial','stdio','-drive',f'file={disk},if=virtio,format=qcow2','-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0','-smbios','type=1,serial=ds=nocloud-net;s=http://10.0.2.2:8765/seed/','-fsdev',f'local,id=out,path={OUT},security_model=none','-device','virtio-9p-pci,fsdev=out,mount_tag=output']
 (OUT/'run.json').write_text(json.dumps({'command':cmd,'disk':str(disk),'output':str(OUT),'resume':args.resume},indent=2)+'\n')
 try:
  with (OUT/'serial.log').open('a') as log:run(cmd,stdout=log,stderr=subprocess.STDOUT)
 finally:server.shutdown()
 status=OUT/'build.exit'
 if not status.exists() or status.read_text().strip()!='0':raise SystemExit('Build incomplete/failed; inspect artifacts/vm-build/serial.log and guest-build.log')
 iso=OUT/'windows12-amd64-preview.iso'
 if not iso.is_file():raise SystemExit('Guest reported success without ISO; refusing success.')
 print('Built',iso,'; boot/install validation remains required.')
if __name__=='__main__':main()
