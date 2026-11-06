import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_localhost', ROOT / 'tools/package_localhost.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PortablePackageTests(unittest.TestCase):
    def setUp(self):
        (ROOT / ".qa").mkdir(exist_ok=True)

    def test_verified_reproducible_package_and_extracted_startup(self):
        qa = ROOT / '.qa'
        qa.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=qa) as temporary:
            directory = Path(temporary)
            first = package.build(directory / 'first.zip')
            second = package.build(directory / 'second.zip')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                self.assertFalse(any('/tests/' in n or '/tools/' in n or '/.qa/' in n or 'progress' in n for n in names))
                for name in ('start.sh', 'Start-macOS.command', 'site/labs/lab-gcc'):
                    self.assertTrue(archive.getinfo('BinarySchool-Localhost/' + name).external_attr >> 16 & 0o111)
                archive.extractall(directory / 'unpacked folder with spaces')
            extracted = directory / 'unpacked folder with spaces/BinarySchool-Localhost'
            manifest = json.loads((extracted / 'SHA256SUMS.json').read_text())
            for name, expected in manifest.items():
                self.assertEqual(hashlib.sha256((extracted / name).read_bytes()).hexdigest(), expected, name)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            process = subprocess.Popen([sys.executable, str(extracted / 'start.py'), '--no-browser', '--port', str(port)], cwd=directory, env=dict(os.environ, PYTHONIOENCODING='ascii'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                for attempt in range(100):
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:{}/__binary_school__/health'.format(port), timeout=1) as response:
                            self.assertEqual(json.load(response)['app'], 'Binary School')
                        break
                    except OSError:
                        if process.poll() is not None:
                            self.fail(process.communicate()[1].decode())
                        time.sleep(0.02)
                else:
                    self.fail('Extracted server did not start')
                for path in ('/', '/curriculum.json', '/labs/lab-gcc'):
                    with urllib.request.urlopen('http://127.0.0.1:{}{}'.format(port, path), timeout=2) as response:
                        self.assertEqual(response.status, 200)
            finally:
                process.terminate()
                process.communicate(timeout=5)

    def test_reject_output_outside_project(self):
        with self.assertRaises(ValueError):
            package.build(ROOT.parent / 'outside.zip')

    def test_reject_changed_source_without_replacing_existing_package(self):
        original = package.ROOT
        with tempfile.TemporaryDirectory(dir=ROOT / '.qa') as temporary:
            fixture = Path(temporary)
            (fixture / 'README.txt').write_text('changed')
            (fixture / 'SHA256SUMS.json').write_text(json.dumps({'README.txt': '0' * 64}))
            output = fixture / 'existing.zip'
            output.write_bytes(b'previous package')
            try:
                package.ROOT = fixture
                with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                    package.build(output)
                self.assertEqual(output.read_bytes(), b'previous package')
            finally:
                package.ROOT = original
