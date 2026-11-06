from pathlib import Path
import json,zipfile,hashlib,os
os.chdir(Path(__file__).resolve().parents[1])
r=Path('site/labs/readiness')
review='''FRESH MOCK FINAL: POST-ATTEMPT SELF-REVIEW
Do not open until you have saved your independent report.
All variants share a structure but differ in constants, encoded token and data.
C sources here are original. Compare your own reconstruction, not naming style.

Variant | threshold | rate | bonus | token
cedar   | 3         | 4    | 5     | north
quartz  | 2         | 6    | 7     | delta
willow  | 4         | 3    | 8     | cabin
The two-field-like appearance can mislead: Policy has THREE int fields at
0,4,8. charge loops over n, charges rate below threshold and rate+2 above it,
subtracts bonus if n>threshold, then adds volatile adjustment (original1).
Repaired output adds9. Correct token + probe0 exits0; failed unlock exits3;
parser errors exit2. Windows additionally prints wide_length=10 and varying PID.

Expected original / repaired charges for quantities 0..8:
'''
import importlib.util
spec=importlib.util.spec_from_file_location('verify',r/'verify-repair.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
for name in mod.VARIANTS:review+=name+': '+', '.join(f'{mod.expected(name,n,1)}/{mod.expected(name,n,9)}' for n in range(9))+'\n'
review+='''
100-point SELF-REVIEW RUBRIC (ungraded)
A: C recovery30: types/layout8, control/data flow10, parsing/returns6,
   edge cases6. Give instruction evidence and explain any inferred type.
B: Windows25: import/startup identification6, observed call arguments/ABI7,
   string/struct interpretation6, correct backed RVA conversion6.
   Static-only analysis is partial; record missing native Windows tests.
C: Debugging20: reproducible breakpoints5, live state5, competing hypotheses5,
   predictions checked across inputs5. Register snapshots without interpretation
   are incomplete. Account for ASLR and optimization.
D: anti-analysis/repair25: decoded data5, explicit toy-probe reasoning5,
   temporary vs persistent change5, computational repair5, regression tests5.
   Verify at least quantities0,1,3,5,8 and invalid/probe/token failure paths.

Use verify-repair.py VARIANT PATH-TO-YOUR-PATCHED-EXECUTABLE locally to check
all9 quantities and7 failure/parser cases. It RUNS the supplied path: use your
own training executable. Run it on the matching OS. Linux cannot run PE itself.
Browser validation accepts the narrow patch of adjustment's initialized data
from1 to9, preserving the rest of the original file; it does not execute it.
Alternative instruction repairs should use the behavioral verifier.

Deduct credit for unsupported claims even if the output happens to match.
Retest a fresh variant after revisiting missed skills. A self-awarded score is
not a verified credential, university grade, or guarantee of exam performance.

MSVC comparison after the attempt: extract this review kit and run
build-msvc-readiness.bat from x86 and x64 Native Tools prompts. Build outputs
are native MSVC, unlike the supplied cross-compiled MinGW GCC PE.
Live Windows/MSVC verification was not available on the build host.
'''
(r/'MOCK-FINAL-REVIEW.txt').write_text(review)
(r/'README.txt').write_text('''BINARY SCHOOL PRACTICAL READINESS LABS
Original investigations: xref, records, trace, windows, protected, reconstruct.
Every program has guided and stripped native Windows x64 PE (MinGW-w64 GCC14)
builds. Portable programs also have GCC Linux x64 ELF builds. The Windows API
investigation deliberately has no Linux ELF substitute. MSVC output is built
locally with build-msvc-readiness.bat in x86/x64 Native Tools prompts.
MSVC and live Windows execution need local verification. PE import tables and
architecture were statically checked; Linux execution was tested.

Fresh final variants cedar/quartz/willow are packaged separately. Start with
mock-final-challenges.zip; open mock-final-review.zip only after the attempt.
Sources are self-review aids, not secret exam material. The website never runs
uploaded programs. All exercises are ungraded; flags/checkpoints give feedback.

Inputs are bounded and programs have no network or file-writing behavior.
On Linux chmod +x the downloaded ELF before execution. On older Linux rebuild
from C if the C runtime is incompatible. ARM hosts need compatible x86 emulation
for execution; Ghidra can statically analyze both ELF and PE without running.

See THIRD-PARTY-NOTICES.txt for MinGW runtime licensing notices.
''')
def zipfiles(name,entries):
 with zipfile.ZipFile(r/name,'w',zipfile.ZIP_DEFLATED) as z:
  for path,arc in entries:z.write(path,arc)
base=[(r/n,n) for n in ['README.txt','THIRD-PARTY-NOTICES.txt','build-msvc-readiness.bat','build-linux-readiness.sh']]
zipfiles('practical-source-kit.zip',base+[(p,'sources/'+p.name) for p in (r/'sources').glob('*.c') if not p.name.startswith('final-')])
entries=[(r/'BRIEF.txt','BRIEF.txt'),(r/'THIRD-PARTY-NOTICES.txt','THIRD-PARTY-NOTICES.txt')]
for variant in ['cedar','quartz','willow']:
 entries += [(p,variant+'/'+p.name) for p in r.glob('final-'+variant+'-*')]
zipfiles('mock-final-challenges.zip',entries)
zipfiles('mock-final-review.zip',base+[(r/'MOCK-FINAL-REVIEW.txt','MOCK-FINAL-REVIEW.txt'),(r/'verify-repair.py','verify-repair.py')]+[(p,'sources/'+p.name) for p in (r/'sources').glob('final-*.c')])
manifest={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(r.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json' and '__pycache__' not in p.parts}
(r/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2)+'\n')
