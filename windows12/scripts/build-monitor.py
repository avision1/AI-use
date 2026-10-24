#!/usr/bin/env python3
"""Persistent, low-frequency build monitor; does not launch or stop the VM.
Use stdin `cleanup` for the separately audited stale-sync-copy cleanup, `status`
for a snapshot, or `stop` to stop only this monitor. Default interval >=60s.
"""
from pathlib import Path
import argparse,json,os,select,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.work/builder';OUT=ROOT/'artifacts/vm-build'
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--interval',type=int,default=60)
 args=parser.parse_args()
 if args.interval<60:raise SystemExit('Use intervals of at least60 seconds around a changing VM disk')
 for path in [WORK,OUT,WORK/'monitor.log']:
  if path.is_symlink() or not path.resolve().is_relative_to(ROOT):raise SystemExit('Monitor path escapes project')
 def emit_status():
  disk=WORK/'build.qcow2';serial=OUT/'serial.log'
  temporary=[p for p in WORK.glob('.build.qcow2.*') if p.is_file() and not p.is_symlink()]
  space=os.statvfs(WORK)
  status={'time':time.time(),'free_bytes':space.f_bavail*space.f_frsize,'disk_allocated':disk.stat().st_blocks*512 if disk.exists() else None,'sync_temp_count':len(temporary),'sync_temp_allocated':sum(p.stat().st_blocks*512 for p in temporary)}
  if serial.exists():
   status['serial_age_seconds']=round(time.time()-serial.stat().st_mtime)
   with serial.open('rb') as source:
    source.seek(max(0,serial.stat().st_size-32768));status['latest_lines']=source.read().decode(errors='replace').splitlines()[-6:]
  result=OUT/'build.exit'
  if result.exists():status['build_exit']=result.read_text().strip()
  line=json.dumps(status)
  with (WORK/'monitor.log').open('a') as destination:destination.write(line+'\n')
  print(line,flush=True)
  return result.exists()
 stdin_open=True
 while True:
  if emit_status():return
  until=time.monotonic()+args.interval
  while time.monotonic()<until:
   if not stdin_open:time.sleep(max(0,until-time.monotonic()));break
   readable,_,_=select.select([sys.stdin],[],[],max(0,until-time.monotonic()))
   if not readable:break
   command=sys.stdin.readline()
   if not command:stdin_open=False;continue
   if command.strip()=='stop':return
   if command.strip()=='status':break
   if command.strip()=='cleanup':
    subprocess.run([sys.executable,'-B',str(ROOT/'scripts/build-clean-sync.py'),'--apply'],check=True)
    break
if __name__=='__main__':main()
