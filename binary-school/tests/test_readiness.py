"""Checks for practical learning contracts, fresh binaries, and persistent repair."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'site/labs/readiness'
spec = importlib.util.spec_from_file_location('verify_repair', LAB/'verify-repair.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

class ReadinessTests(unittest.TestCase):
    def test_setup_before_first_challenge_and_practical_downloads(self):
        data = json.loads((ROOT/'site/curriculum.json').read_text())
        self.assertEqual(data['lessons'][0]['id'], 0)
        self.assertEqual(set(range(137)), {l['id'] for l in data['lessons']})
        self.assertEqual(len(data['courseLabs']), 13)
        for lesson in data['lessons']:
            for _, path in lesson.get('practical', {}).get('downloads', []):
                self.assertTrue((ROOT/'site'/path).is_file(), path)
        self.assertIn('Apple Silicon', json.dumps(data['lessons'][0]))

    def test_challenge_pack_has_fresh_binaries_and_no_answers(self):
        with zipfile.ZipFile(LAB/'mock-final-challenges.zip') as pack:
            names = pack.namelist()
            self.assertEqual(sum(n.endswith('.exe') for n in names), 6)
            self.assertEqual(sum(n.endswith('linux-x64') for n in names), 6)
            self.assertFalse(any(n.endswith(('.c','.py','.json')) for n in names))
            self.assertNotIn('north', pack.read('BRIEF.txt').decode())
            for name in names:
                if name.endswith('.exe'): self.assertEqual(pack.read(name)[:2], b'MZ')
                if name.endswith('linux-x64'): self.assertEqual(pack.read(name)[:4], b'\x7fELF')
        with zipfile.ZipFile(LAB/'mock-final-review.zip') as pack:
            self.assertIn('sources/final-cedar.c',pack.namelist())
            self.assertIn('verify-repair.py',pack.namelist())
        with zipfile.ZipFile(LAB/'practical-source-kit.zip') as pack:
            self.assertFalse(any('final-' in n for n in pack.namelist()))

    def test_pe_architecture_imports_and_checksums(self):
        manifest=json.loads((LAB/'SHA256SUMS.json').read_text())
        for name, digest in manifest.items():
            data=(LAB/name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),digest,name)
            if name.endswith('.exe'):
                offset=struct.unpack_from('<I',data,0x3c)[0]
                self.assertEqual(data[offset:offset+4],b'PE\0\0')
                self.assertEqual(struct.unpack_from('<H',data,offset+4)[0],0x8664)
        for build in ('guided','independent'):
            data=(LAB/f'windows-{build}-mingw-x64.exe').read_bytes()
            for api in (b'GetCurrentProcessId',b'IsDebuggerPresent',b'lstrcmpA',b'lstrlenW'):
                self.assertIn(api,data)

    @unittest.skipUnless(platform.system()=='Linux' and platform.machine() in ('x86_64','AMD64'), 'requires native Linux x64')
    def test_guided_and_stripped_practical_behavior(self):
        cases={
            'xref':[(['orbit','0'],1,'result=0'),(['orbit','2'],0,'BS{practical_xrefs}'),(['orbit','3'],0,'BS{practical_xrefs}'),(['wrong','2'],1,'result=-1'),(['orbit','5'],1,'result=-1')],
            'records':[(['0'],1,'total=0'),(['1'],1,'total=9'),(['2'],1,'total=9'),(['3'],0,'BS{practical_records}'),(['4'],2,None)],
            'trace':[(['3','-3','4'],0,'BS{practical_watchpoint}'),(['3','3','4'],1,'total=25'),(['0','0','0'],1,'total=4'),(['bad','0','0'],2,None)],
            'protected':[(['maple','0'],0,'BS{practical_decoding}'),(['maple','1'],3,'ANALYSIS_PATH'),(['wrong','0'],1,None),(['maple','bad'],2,None)],
            'reconstruct':[(['0','0'],1,'price=0'),(['0','2'],1,'price=6'),(['0','4'],1,'price=14'),(['1','3'],1,'price=15'),(['1','5'],0,'BS{practical_reconstruction}'),(['2','4'],2,None)]
        }
        for name, entries in cases.items():
            for build in ('guided','independent'):
                binary=LAB/f'{name}-{build}-linux-x64'
                for args, code, text in entries+[([],2,None),(['x'*100],2,None)]:
                    with self.subTest(name=name,build=build,args=args):
                        result=subprocess.run([str(binary)]+args,capture_output=True,text=True,timeout=3)
                        self.assertEqual(result.returncode,code)
                        if text:self.assertIn(text,result.stdout)

    @unittest.skipUnless(platform.system()=='Linux' and platform.machine() in ('x86_64','AMD64'), 'requires native Linux x64')
    def test_fresh_final_original_and_persistent_repair(self):
        manifest=json.loads((LAB/'repair-manifest.json').read_text())
        for filename, metadata in manifest.items():
            data=(LAB/filename).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),metadata['original'])
            self.assertEqual(data[metadata['offset']:metadata['offset']+4],struct.pack('<i',1))
            patched=bytearray(data);patched[metadata['offset']:metadata['offset']+4]=struct.pack('<i',9)
            self.assertEqual(hashlib.sha256(patched).hexdigest(),metadata['patched'])
            if not filename.endswith('linux-x64'):continue
            variant=filename.split('-')[1]
            for n in range(9):
                result=subprocess.run([str(LAB/filename),str(n),verifier.VARIANTS[variant][3],'0'],capture_output=True,text=True,timeout=3)
                self.assertEqual(result.returncode,0)
                self.assertEqual(result.stdout,'charge={}\n'.format(verifier.expected(variant,n,1)))
            with tempfile.TemporaryDirectory(dir=ROOT/'tests') as folder:
                executable=Path(folder)/'patched';executable.write_bytes(patched);executable.chmod(0o755)
                self.assertEqual(verifier.check(variant,executable),16)

if __name__=='__main__':unittest.main()
