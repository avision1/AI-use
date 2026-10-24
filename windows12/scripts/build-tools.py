#!/usr/bin/env python3
"""Extract signature-verified Ubuntu VM or ISO build tools locally; never install packages.
Only supports amd64 Ubuntu 24.04 host. Uses apt signed metadata but no apt state.
"""
from pathlib import Path
import hashlib, lzma, os, re, subprocess, json, sys
from concurrent.futures import ThreadPoolExecutor
import tarfile, io, argparse, fcntl, errno, stat
ROOT=Path(__file__).resolve().parents[1]
def bounded(path):
 if not path.resolve().is_relative_to(ROOT):raise SystemExit('Path escapes project: '+str(path))
 return path
WORK=bounded(ROOT/'.work/builder')
TOOLS=WORK/'tools'
ENV=os.environ.copy()
WRITABLE_ENV={'HOME':WORK/'home','TMPDIR':WORK/'tmp','XDG_CACHE_HOME':WORK/'cache','GNUPGHOME':WORK/'gnupg','XDG_CONFIG_HOME':WORK/'config','XDG_DATA_HOME':WORK/'data','XDG_STATE_HOME':WORK/'state'}
def run(args,**kw):return subprocess.run(args,check=True,env=ENV,**kw)
def get(url,path):
 bounded(path);partial=bounded(Path(str(path)+'.part'))
 if path.is_symlink() or partial.is_symlink():raise SystemExit('Download symlink refused')
 if not path.exists():run(['curl','--fail','--location','--retry','2','--max-time','180','--output',str(path)+'.part',url]);Path(str(path)+'.part').rename(path)
def fields(block):
 d={}
 for line in block.splitlines():
  if line and not line.startswith(' ') and ': ' in line:
   k,v=line.split(': ',1);d[k]=v
 return d
def main():
 global TOOLS
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--profile',choices=['vm','iso'],default='vm',help='vm: QEMU; iso: separate read-only ISO inspection tools')
 arguments=parser.parse_args()
 TOOLS=WORK/('tools' if arguments.profile=='vm' else 'iso-tools')
 if TOOLS.is_symlink() or not TOOLS.resolve().is_relative_to(ROOT):raise SystemExit('Tool destination escapes project or aliases another toolset')
 for path in [WORK,TOOLS,WORK/'debs',ROOT/'build',*WRITABLE_ENV.values()]:bounded(path)
 for key,value in WRITABLE_ENV.items():value.mkdir(parents=True,exist_ok=True);ENV[key]=str(value)
 if arguments.profile=='vm':
  lock=WORK/'runner.lock'
  if lock.is_symlink():raise SystemExit('Runner lock symlink refused')
  runner_lock=lock.open('a')
  try:fcntl.flock(runner_lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:raise SystemExit('A build runner is active; never overwrite its mapped QEMU tools')
  qmp=WORK/'qmp.in'
  if qmp.is_symlink() or (qmp.exists() and not stat.S_ISFIFO(qmp.stat().st_mode)):raise SystemExit('Unexpected QMP control; reconcile before replacing VM tools')
  if qmp.exists():
   try:listener=os.open(qmp,os.O_WRONLY|os.O_NONBLOCK)
   except OSError as error:
    if error.errno!=errno.ENXIO:raise SystemExit('Cannot reconcile QMP listener')
   else:
    os.close(listener);raise SystemExit('A VM has live QMP controls; never overwrite its mapped QEMU tools')

 host=dict(line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
 if host.get('ID','').strip(chr(34))!='ubuntu' or host.get('VERSION_ID','').strip(chr(34))!='24.04':sys.exit('Bootstrap requires Ubuntu 24.04; supply a host-compatible QEMU instead.')
 if os.uname().machine!='x86_64':sys.exit('Local bootstrap requires x86_64; provide a host-compatible QEMU instead.')
 packages={}
 for suite in ['noble','noble-updates','noble-security']:
  base='https://security.ubuntu.com/ubuntu' if suite.endswith('security') else 'https://archive.ubuntu.com/ubuntu'
  rel=WORK/f'{suite}-InRelease';get(f'{base}/dists/{suite}/InRelease',rel)
  run(['gpgv','--homedir',str(WORK/'gnupg'),'--keyring','/usr/share/keyrings/ubuntu-archive-keyring.gpg',str(rel)])
  ix=WORK/f'{suite}-Packages.xz';get(f'{base}/dists/{suite}/main/binary-amd64/Packages.xz',ix)
  match=re.search(r'^ ([0-9a-f]{64})\s+\d+ main/binary-amd64/Packages.xz$',rel.read_text(),re.M)
  if not match or hashlib.sha256(ix.read_bytes()).hexdigest()!=match[1]:sys.exit('Signed Packages SHA256 mismatch: '+suite)
  for block in lzma.open(ix,'rt').read().split('\n\n'):
   f=fields(block)
   if 'Package' in f: f['base']=base;packages.setdefault(f['Package'],[]).append(f)
 actual_names=set(packages)
 for candidates in list(packages.values()):
  for candidate in candidates:
   for provided in candidate.get('Provides','').split(','):
    alias=provided.strip().split(' ')[0]
    if alias and alias not in actual_names:
     provider=candidate.copy();declared=re.search(r'\(= ([^)]+)\)',provided)
     provider['_ProvidedVersion']=declared[1] if declared else None
     packages.setdefault(alias,[]).append(provider)
 todo=['qemu-system-x86','qemu-utils','seabios'] if arguments.profile=='vm' else ['xorriso','squashfs-tools'];selected={};constraints=[]
 while todo:
  name=todo.pop()
  if name in selected:continue
  if name not in packages:sys.exit('Dependency unavailable in authenticated main index: '+name)
  candidates=packages[name]
  if name not in actual_names and len({f['Package'] for f in candidates})!=1:sys.exit('Ambiguous virtual dependency requires explicit selection: '+name)
  f=candidates[0]
  for candidate in candidates[1:]:
   if subprocess.run(['dpkg','--compare-versions',candidate['Version'],'gt',f['Version']],env=ENV).returncode==0:f=candidate
  selected[name]=f
  for dep in (f.get('Pre-Depends','')+','+f.get('Depends','')).split(','):
   choices=[re.split(r'[ (:\[]',s.strip())[0] for s in dep.split('|') if s.strip()]
   if choices:
    chosen=next((x for x in choices if x in packages),None)
    if not chosen:sys.exit('Unresolved dependency: '+dep)
    predicate=re.search(r'\((>=|<=|=|<<|>>) ([^)]+)\)',next(s for s in dep.split('|') if s.strip().split()[0].split(':')[0]==chosen))
    if predicate:
     constraints.append((chosen,predicate[1],predicate[2]))
     versions=packages[chosen]
     if not any(subprocess.run(['dpkg','--compare-versions',v['Version'] if chosen in actual_names else v['_ProvidedVersion'],predicate[1],predicate[2]],env=ENV).returncode==0 for v in versions if (v['Version'] if chosen in actual_names else v.get('_ProvidedVersion')) is not None):sys.exit('Unsatisfied version constraint: '+dep)
    todo.append(chosen)
 for name,operator,version in constraints:
  if subprocess.run(['dpkg','--compare-versions',selected[name]['Version'] if name in actual_names else selected[name]['_ProvidedVersion'],operator,version],env=ENV).returncode!=0:sys.exit('Selected dependency version conflicts: '+name+' '+operator+' '+version)
 TOOLS.mkdir(parents=True,exist_ok=True)
 bounded(WORK/'debs').mkdir(exist_ok=True)
 def download(item):
  name,f=item;deb=WORK/'debs'/Path(f['Filename']).name;get(f['base']+'/'+f['Filename'],deb)
  if hashlib.sha256(deb.read_bytes()).hexdigest()!=f['SHA256']:raise RuntimeError('Package SHA256 mismatch: '+name)
  return deb
 with ThreadPoolExecutor(max_workers=6) as pool:
  unique={f['Filename']:(name,f) for name,f in selected.items()}
  archives=list(pool.map(download,unique.values()))
 for deb in archives:
  payload=run(['dpkg-deb','--fsys-tarfile',str(deb)],stdout=subprocess.PIPE).stdout
  with tarfile.open(fileobj=io.BytesIO(payload)) as tf:
   members=[m for m in tf.getmembers() if not (m.issym() and Path(m.linkname).is_absolute())]
   tf.extractall(TOOLS,members=members,filter='data')
 lock_output=bounded(ROOT/'build'/('tools-lock.json' if arguments.profile=='vm' else 'iso-tools-lock.json'))
 if lock_output.is_symlink():raise SystemExit('Tool lock output symlink refused')
 lock_output.write_text(json.dumps({n:{k:v for k,v in f.items() if k in ['Package','Version','Filename','SHA256','base']} for n,f in selected.items()},indent=2)+'\n')
 print('Project-local '+arguments.profile+' tools extracted to',TOOLS)
if __name__=='__main__':main()
