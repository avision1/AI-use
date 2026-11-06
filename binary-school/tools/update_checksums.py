"""Refresh project integrity manifests; optional --packages refreshes changed lab ZIPs."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import zipfile
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.build-tools','__pycache__','.openai','.venv','.qa'}
def manifest(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and not any(part in EXCLUDED for part in p.relative_to(root).parts)
            and p != root/'SHA256SUMS.json'}
def write_manifest(root):
    (root/'SHA256SUMS.json').write_text(json.dumps(manifest(root),indent=2)+'\n')
def pack(folder,target,prefix=''):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file() and not any(part in EXCLUDED for part in p.relative_to(folder).parts):
                z.write(p,prefix+p.relative_to(folder).as_posix())
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--packages',action='store_true');args=parser.parse_args()
    if args.packages:
        labs=ROOT/'site/labs'
        for name,archive,prefix in [('flags','interactive-flag-labs.zip',''),('full','binary-school-full-labs.zip','binary-school-labs/'),('windows-acceptance','windows-acceptance-kit.zip','site/labs/windows-acceptance/')]:
            folder=labs/name;write_manifest(folder);pack(folder,labs/archive,prefix)
    write_manifest(ROOT)
