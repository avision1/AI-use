import subprocess,sys
if len(sys.argv)!=2: raise SystemExit("Usage: python3 check_repair.py ./YOUR_PATCHED_FILE")
for x in [-10,-1,0,1,4,10]:
 r=subprocess.run([sys.argv[1],str(x)],capture_output=True,text=True,timeout=3)
 assert r.returncode==0 and r.stdout==f"fee={x*3+9}\n",(x,r.returncode,r.stdout)
for x in ["abc","11","-11",""]:
 r=subprocess.run([sys.argv[1],x],capture_output=True,timeout=3)
 assert r.returncode==2, x
print("Repair behavior passed all supplied cases. This is not proof for arbitrary inputs.")
