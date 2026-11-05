import subprocess,sys
if len(sys.argv)!=3: raise SystemExit("Usage: python3 compare.py ORIGINAL RECONSTRUCTED")
inputs=["-10","-1","0","1","2","3","4","5","6","7","8","10","100","abc",""]
failures=0
for x in inputs:
 a=subprocess.run([sys.argv[1],x],capture_output=True,timeout=3)
 b=subprocess.run([sys.argv[2],x],capture_output=True,timeout=3)
 ok=(a.returncode,a.stdout,a.stderr)==(b.returncode,b.stdout,b.stderr)
 print(repr(x),"MATCH" if ok else "DIFFERENCE")
 failures+=not ok
raise SystemExit(bool(failures))
