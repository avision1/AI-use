from pathlib import Path
import subprocess,json,hashlib,zipfile,struct,os,argparse
os.chdir(Path(__file__).resolve().parents[1])
parser=argparse.ArgumentParser(description='Rebuild original practical and holdout GCC ELF/MinGW PE binaries. Requires both compilers; not needed to run the website.')
parser.add_argument('--mingw-cc',default='x86_64-w64-mingw32-gcc')
args=parser.parse_args()
Path('.build-tools').mkdir(exist_ok=True)
r=Path('site/labs/readiness'); cc=Path(__import__('shutil').which(args.mingw_cc) or args.mingw_cc).resolve()
manifest={}; layout={}
for source in sorted((r/'sources').glob('*.c')):
 name=source.stem
 for platform,compiler in [('linux-x64','gcc'),('mingw-x64.exe',str(cc))]:
  if name=='windows' and platform.startswith('linux'):continue
  for kind,opts in [('guided',['-O0','-g']),('independent',['-O2','-s'])]:
   out=r/f'{name}-{kind}-{platform}'
   args=[compiler,'-std=c11','-Wall','-Wextra','-static-libgcc',*opts,str(source),'-o',str(out)]
   subprocess.run(args,check=True)
   if platform=='linux-x64':out.chmod(0o755)
   if name.startswith('final-'):
    # Resolve the global's virtual address and convert using section headers.
    # For stripped builds derive the address from a temporary matching unstripped link.
    symbol_binary=out
    if kind=='independent':
     symbol_binary=Path('.build-tools')/out.name
     subprocess.run([a for a in args if a!='-s'][:-1]+[str(symbol_binary)],check=True)
    nm='nm' if platform=='linux-x64' else str(cc.parent/'x86_64-w64-mingw32-nm')
    objdump='objdump' if platform=='linux-x64' else str(cc.parent/'x86_64-w64-mingw32-objdump')
    symbols=subprocess.check_output([nm,str(symbol_binary)],text=True)
    address=int(next(line.split()[0] for line in symbols.splitlines() if line.endswith(' adjustment')),16)
    headers=subprocess.check_output([objdump,'-h',str(out)],text=True)
    off=None
    for line in headers.splitlines():
     cols=line.split()
     if len(cols)>=7 and cols[0].isdigit():
      size,vma,fileoff=int(cols[2],16),int(cols[3],16),int(cols[5],16)
      if vma<=address<vma+size:off=fileoff+address-vma;break
    data=out.read_bytes()
    assert data[off:off+4]==struct.pack('<i',1),(out,off)
    patched=bytearray(data);patched[off:off+4]=struct.pack('<i',9)
    manifest[out.name]={'original':hashlib.sha256(data).hexdigest(),'patched':hashlib.sha256(patched).hexdigest(),'offset':off}
(r/'repair-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

# Regenerate the download ZIPs and checksums after rebuilding.
subprocess.run([__import__("sys").executable,"tools/package_readiness.py"],check=True)
