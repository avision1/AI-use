#!/usr/bin/env python3
"""Query, pause, explicitly resume or stop the contained build VM via local QMP."""
from pathlib import Path
import argparse,fcntl,json,os,re,select,stat,time
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.work/builder'
def safe(path):
 if path.is_symlink() or not path.resolve().is_relative_to(ROOT):raise SystemExit('QMP path escapes project: '+str(path))
 return path
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('command',choices=['status','blockstats','chardevs','console-ringbuf','console-read','registers','pause','resume','powerdown','quit'],default='status',nargs='?')
 parser.add_argument('--reason',default='Explicit operator request')
 parser.add_argument('--console-id',help='Explicit observed UART ID serialN required for console actions; never the QMP control backend')
 args=parser.parse_args()
 if args.command in ['console-ringbuf','console-read'] and args.console_id is None:parser.error('Console actions require explicit --console-id from the observed chardevs response')
 args.console_id=args.console_id or 'serial0'
 if not re.fullmatch(r'serial[0-9]{1,3}',args.console_id):parser.error('--console-id must be an observed UART ID serialN')
 safe(WORK)
 pipe=WORK/'qmp'
 for suffix in ['.in','.out']:
  path=safe(Path(str(pipe)+suffix))
  if not path.exists() or not stat.S_ISFIFO(path.stat().st_mode):raise SystemExit('No valid project-local QMP FIFO: '+str(path))
 with safe(WORK/'qmp-client.lock').open('a') as lock:
  deadline=time.monotonic()+5
  while True:
   try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);break
   except BlockingIOError:
    if time.monotonic()>deadline:raise SystemExit('Another QMP client is active; retry after reconciliation')
    time.sleep(0.1)
  reader=os.open(str(pipe)+'.out',os.O_RDONLY|os.O_NONBLOCK)
  try:writer=os.open(str(pipe)+'.in',os.O_WRONLY|os.O_NONBLOCK)
  except OSError:os.close(reader);raise SystemExit('No VM is listening on QMP')
  commands={'status':{'execute':'query-status'},'blockstats':{'execute':'query-blockstats'},'chardevs':{'execute':'query-chardev'},'console-ringbuf':{'execute':'chardev-change','arguments':{'id':args.console_id,'backend':{'type':'ringbuf','data':{'size':1048576}}}},'console-read':{'execute':'ringbuf-read','arguments':{'device':args.console_id,'size':16384,'format':'base64'}},'registers':{'execute':'human-monitor-command','arguments':{'command-line':'info registers'}},'pause':{'execute':'stop'},'resume':{'execute':'cont'},'powerdown':{'execute':'system_powerdown'},'quit':{'execute':'quit'}}
  identifier='requested-'+str(time.time_ns())
  requested=commands[args.command];requested['id']=identifier
  for command in [{'execute':'qmp_capabilities'},requested]:os.write(writer,(json.dumps(command)+'\n').encode())
  buffer=b'';deadline=time.monotonic()+5
  try:
   while time.monotonic()<deadline:
    if not select.select([reader],[],[],0.5)[0]:continue
    chunk=os.read(reader,65536)
    if not chunk:break
    buffer+=chunk
    while b'\n' in buffer:
     line,buffer=buffer.split(b'\n',1)
     try:response=json.loads(line)
     except ValueError:continue
     if response.get('id')!=identifier:continue
     print(json.dumps(response,indent=2))
     if 'error' in response:raise SystemExit('QMP rejected the requested command')
     if args.command in ['pause','resume']:
      event={'time':time.time(),'paused':args.command=='pause','reason':args.reason,'scope':'Only the main project QEMU guest CPUs; host unchanged','requires_explicit_resume':args.command=='pause'}
      try:
       marker=safe(WORK/'paused-state.json');pending=safe(WORK/'paused-state.pending.json')
       pending.write_text(json.dumps(event,indent=2)+'\n');pending.replace(marker)
       with safe(WORK/'pause-events.jsonl').open('a') as audit:audit.write(json.dumps(event)+'\n')
      except (OSError,SystemExit) as error:
       print('QMP '+args.command+' succeeded, but state/audit could not be recorded: '+str(error),flush=True)
     return
   raise SystemExit('No matching QMP response within five seconds')
  finally:os.close(reader);os.close(writer)
if __name__=='__main__':main()
