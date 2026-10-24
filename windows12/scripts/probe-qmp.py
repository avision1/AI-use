#!/usr/bin/env python3
"""Query or stop the contained build VM through project-local QMP FIFOs."""
from pathlib import Path
import argparse,json,os,select,stat,time
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('command',choices=['status','registers','quit'],default='status',nargs='?')
 args=parser.parse_args()
 pipe=ROOT/'.work/builder/qmp'
 for suffix in ['.in','.out']:
  p=Path(str(pipe)+suffix)
  if p.is_symlink() or not p.resolve().is_relative_to(ROOT) or not p.exists() or not stat.S_ISFIFO(p.stat().st_mode):raise SystemExit('No valid project-local QMP FIFO: '+str(p))
 r=os.open(str(pipe)+'.out',os.O_RDONLY|os.O_NONBLOCK)
 try:w=os.open(str(pipe)+'.in',os.O_WRONLY|os.O_NONBLOCK)
 except OSError:os.close(r);raise SystemExit('No VM is listening on QMP')
 commands={'status':{'execute':'query-status'},'registers':{'execute':'human-monitor-command','arguments':{'command-line':'info registers'}},'quit':{'execute':'quit'}}
 requested=commands[args.command];requested['id']='requested'
 for command in [{'execute':'qmp_capabilities','id':'capabilities'},requested]:os.write(w,(json.dumps(command)+'\n').encode())
 buffer=b'';deadline=time.monotonic()+5
 try:
  while time.monotonic()<deadline:
   if not select.select([r],[],[],0.5)[0]:continue
   chunk=os.read(r,65536)
   if not chunk:break
   buffer+=chunk
   while b'\n' in buffer:
    line,buffer=buffer.split(b'\n',1)
    response=json.loads(line)
    if response.get('id')=='requested':
     print(json.dumps(response,indent=2));return
  raise SystemExit('No matching QMP response within five seconds')
 finally:os.close(r);os.close(w)
if __name__=='__main__':main()
