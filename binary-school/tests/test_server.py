import importlib.util
import json
import pathlib
import threading
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binary_school_server', ROOT / 'start.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class LocalPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app.http.server.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:{}/'.format(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def get(self, path, method='GET'):
        return urllib.request.urlopen(urllib.request.Request(self.base+path, method=method), timeout=3)

    def test_home_and_local_assets(self):
        for path in ('', 'app.js', 'style.css', 'curriculum.json'):
            with self.get(path) as r:
                self.assertEqual(r.status, 200)
                self.assertGreater(len(r.read()), 100)
        css = (ROOT / 'site/style.css').read_text()
        self.assertNotIn('@import', css)

    def test_health_and_head(self):
        with self.get('__binary_school__/health') as r:
            self.assertEqual(json.load(r)['edition'], 'localhost')
        with self.get('curriculum.json', 'HEAD') as r:
            self.assertEqual(r.read(), b'')
            self.assertEqual(r.headers['Cache-Control'], 'no-store')

    def test_curriculum_and_downloads(self):
        with self.get('curriculum.json') as r:
            data = json.load(r)
        self.assertEqual(len(data['lessons']), 137)
        self.assertEqual(len(data['courses']), 13)
        self.assertEqual(len(set(l['id'] for l in data['lessons'])), 137)
        self.assertEqual(len(data['courseLabs']), 13)
        self.assertEqual(sum(bool(l.get('flagDigest')) for l in data['lessons']), 13)
        for l in data['lessons']:
            for label,path in l.get('downloads', []):
                self.assertTrue((ROOT / 'site' / path).is_file(), path)
            if l.get('lab'):
                self.assertTrue((ROOT / 'site/labs/full' / l['lab']).is_file(), l['lab'])
        with self.get('labs/binary-school-full-labs.zip') as r:
            self.assertEqual(r.read()[:2], b'PK')
        with self.get('labs/final-gcc') as r:
            binary = r.read()
            self.assertEqual(binary[:4], b'\x7fELF')
            self.assertEqual(binary.count(b'STATUS=PENDING'), 1)
        with self.get('labs/full/constructs.c') as r:
            self.assertIn('text/plain', r.headers['Content-Type'])

    def test_private_paths_and_listing_not_served(self):
        for path in ('../README.txt', '%2e%2e/README.txt', '%2e%2e%5cREADME.txt', 'labs/', 'labs/full/', 'missing.html', 'start.py'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.get(path)
            self.assertIn(error.exception.code, (403, 404))

    def test_no_write_endpoint(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('curriculum.json', 'POST')
        self.assertEqual(error.exception.code, 501)

    def test_study_uses_local_data(self):
        js = (ROOT / 'site/app.js').read_text()
        self.assertIn("fetch('curriculum.json')", js)
        self.assertIn("fetch('labs/final-gcc')", js)
        self.assertIn('localStorage', js)
        self.assertIn('youtube-nocookie.com', js)
        self.assertNotIn('chatgpt.site', js)

if __name__ == '__main__':
    unittest.main()
