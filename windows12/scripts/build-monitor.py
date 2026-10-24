#!/usr/bin/env python3
"""Persistent build monitor. Auto-clean only reviewed stale sync copies; pause
only main VM CPUs if cleanup cannot retain6GiB. Never automatically resume.
Use a TTY-backed tool session for stdin commands cleanup/status/pause-vm/
resume-vm/vm-status/stop. stop ends only this monitor, not the guest.
"""
from pathlib import Path
import argparse,json,os,select,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.work/builder';OUT=ROOT/'artifacts/vm-build'
def safe(path):
 if path.is_symlink() or not path.resolve().is_relative_to(ROOT):raise SystemExit('Monitor path escapes project')
 return path
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--interval',type=int,default=60)
 parser.add_argument('--auto-cleanup',action='store_true')
 args=parser.parse_args()
 if args.interval<60:raise SystemExit('Use intervals of at least60 seconds around a changing VM disk')
 for path in [WORK,OUT,WORK/'monitor.log']:safe(path)
 env=os.environ.copy()
 for key,name in [('HOME','home'),('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_STATE_HOME','state')]:env[key]=str(safe(WORK/name))
 env['PYTHONDONTWRITEBYTECODE']='1'
 def emit(value):
  line=json.dumps(value)
  try:
   with safe(WORK/'monitor.log').open('a') as destination:destination.write(line+'\n')
  except OSError as error:
   value=dict(value,monitor_log_error=str(error));line=json.dumps(value)
  try:print(line,flush=True)
  except OSError:pass
 def free_bytes():
  space=os.statvfs(WORK);return space.f_bavail*space.f_frsize
 def qmp(command,reason='Explicit monitor operator request'):
  result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/probe-qmp.py'),command,'--reason',reason],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  emit({'time':time.time(),'qmp_command':command,'returncode':result.returncode,'response':result.stdout})
  return result.returncode==0
 def cleanup():
  result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/build-clean-sync.py'),'--apply'],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  emit({'time':time.time(),'cleanup_returncode':result.returncode,'result':result.stdout})
  if free_bytes()<6*1024**3:
   reason='Cleanup failed or free space below6GiB after cleanup: '+str(free_bytes())+' bytes'
   confirmed=qmp('pause',reason)
   if not confirmed:
    record={'time':time.time(),'paused':'unconfirmed','reason':reason,'scope':'QMP stop attempted only for main guest; no host changes','requires_explicit_reconciliation':True}
    try:
     pending=safe(WORK/'paused-state.pending.json')
     pending.write_text(json.dumps(record,indent=2)+'\n');pending.replace(safe(WORK/'paused-state.json'))
    except OSError as error:emit({'pause_marker_error':str(error),'pause_status':'unconfirmed'})
   emit({'time':time.time(),'resource_pause_confirmed':confirmed,'free_bytes':free_bytes(),'requires_explicit_resume':True})
 def emit_status():
  disk=safe(WORK/'build.qcow2');serial=safe(OUT/'serial.log')
  temporary=[]
  for path in WORK.glob('.build.qcow2.*'):
   try:
    if path.is_file() and not path.is_symlink():temporary.append(path.stat().st_blocks*512)
   except FileNotFoundError:continue
  status={'time':time.time(),'free_bytes':free_bytes(),'disk_allocated':disk.stat().st_blocks*512 if disk.exists() else None,'sync_temp_count':len(temporary),'sync_temp_allocated':sum(temporary),'auto_cleanup':args.auto_cleanup}
  if serial.exists():
   status['serial_age_seconds']=round(time.time()-serial.stat().st_mtime)
   with serial.open('rb') as source:
    source.seek(max(0,serial.stat().st_size-32768));status['latest_lines']=source.read().decode(errors='replace').splitlines()[-6:]
  marker=safe(WORK/'paused-state.json')
  if marker.exists():
   try:status['pause_marker']=json.loads(marker.read_text())
   except (OSError,ValueError,UnicodeError) as error:status['pause_marker_error']=str(error)
  result=safe(OUT/'build.exit')
  if result.exists():status['build_exit']=result.read_text().strip()
  emit(status)
  return result.exists()
 stdin_open=True
 while True:
  if args.auto_cleanup and not (OUT/'build.exit').exists():cleanup()
  if emit_status():return
  until=time.monotonic()+args.interval
  while time.monotonic()<until:
   if not stdin_open:time.sleep(max(0,until-time.monotonic()));break
   readable,_,_=select.select([sys.stdin],[],[],max(0,until-time.monotonic()))
   if not readable:break
   command=sys.stdin.readline()
   if not command:stdin_open=False;continue
   command=command.strip()
   if command=='stop':return
   if command=='status':break
   if command=='cleanup':cleanup();break
   if command in ['pause-vm','resume-vm','vm-status']:
    qmp({'pause-vm':'pause','resume-vm':'resume','vm-status':'status'}[command]);break
if __name__=='__main__':main()
