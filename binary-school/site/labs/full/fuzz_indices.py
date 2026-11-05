import subprocess,sys
if len(sys.argv)!=2: raise SystemExit("Usage: python3 fuzz_indices.py ./audit-san")
for mode in ["unsafe","safe"]:
 for n in [-100,-2,-1,0,1,2,3,4,5,9,100]:
  r=subprocess.run([sys.argv[1],mode,str(n)],capture_output=True,timeout=3)
  issue=b"Sanitizer" in r.stderr or b"runtime error:" in r.stderr or r.returncode<0
  print(mode,n,"DIAGNOSTIC" if issue else "REJECT" if r.returncode==2 else "OK")
  if issue: print(r.stderr.decode(errors="replace")[:800])
