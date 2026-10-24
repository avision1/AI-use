#!/usr/bin/env python3
"""Audit/remove only stale workspace-sync copies of this project's build disk.
No configured disks, images, logs, directories or symlinks are removed.
"""
from pathlib import Path
import argparse,json,os,stat,time
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'.work/builder'
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--apply',action='store_true',help='Remove eligible generated temporary copies')
 args=parser.parse_args()
 if not WORK.resolve().is_relative_to(ROOT):raise SystemExit('Work directory escapes project')
 log=WORK/'sync-temp-cleanup.jsonl'
 if log.is_symlink() or not log.resolve().is_relative_to(ROOT):raise SystemExit('Cleanup audit path escapes project')
 protected=set()
 for name in ['build.qcow2','debian-13-genericcloud-amd64.qcow2']:
  path=WORK/name
  if path.exists():
   info=path.stat();protected.add((info.st_dev,info.st_ino))
 cutoff=time.time()-120;removed=0;allocated=0
 before=os.statvfs(WORK);free_before=before.f_bavail*before.f_frsize
 for path in sorted(WORK.glob('.build.qcow2.*')):
  info=path.lstat()
  if not stat.S_ISREG(info.st_mode) or (info.st_dev,info.st_ino) in protected or info.st_mtime>cutoff:continue
  latest=path.lstat()
  if (latest.st_dev,latest.st_ino,latest.st_size,latest.st_mtime_ns)!=(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns):continue
  entry={'time':time.time(),'name':path.name,'size':info.st_size,'allocated':info.st_blocks*512,'mtime':info.st_mtime,'action':'removed' if args.apply else 'eligible'}
  if args.apply:
   path.unlink()
   with log.open('a') as destination:destination.write(json.dumps(entry)+'\n')
  removed+=1;allocated+=info.st_blocks*512
 after=os.statvfs(WORK);free_after=after.f_bavail*after.f_frsize
 print(json.dumps({'applied':args.apply,'eligible_files':removed,'allocated_bytes':allocated,'observed_free_delta':free_after-free_before,'audit_log':str(log)},indent=2))
if __name__=='__main__':main()
