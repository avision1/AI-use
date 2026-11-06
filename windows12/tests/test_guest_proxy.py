"""Proxy transport checks; run only inside the contained test/build VM."""
from contextlib import contextmanager
from pathlib import Path
import runpy
import socket
import threading
import unittest
from urllib.parse import urlsplit
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]


class GuestProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path('/run/windows12-build-vm').is_file():
            raise unittest.SkipTest('Runtime checks require the contained build VM')
        cls.Proxy = runpy.run_path(str(PROJECT / 'scripts/guest-proxy.py'))['GuestProxy']

    @contextmanager
    def upstream(self, respond):
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(3)
        errors = []

        def serve():
            try:
                with listener.accept()[0] as stream:
                    stream.settimeout(3)
                    respond(stream)
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        try:
            yield listener.getsockname()
        finally:
            listener.close()
            thread.join(timeout=4)
            self.assertFalse(thread.is_alive(), 'Fake upstream did not stop')
            if errors:
                raise errors[0]

    def test_empty_and_loopback_proxy_do_not_start_relay(self):
        for url, expected in (('', ''), ('http://localhost:8080', 'http://10.0.2.2:8080'),
                              ('http://127.0.0.1:3128/', 'http://10.0.2.2:3128')):
            with self.subTest(url=url), self.Proxy(url) as relay:
                self.assertEqual(relay.guest_url, expected)
                self.assertIsNone(relay._listener)

    def test_unsupported_urls_fail_without_echoing_secrets(self):
        for url in ('https://proxy:443', 'socks5://proxy:1080', 'http://user:secret@proxy:8080',
                    'http://proxy:8080/path', 'http://proxy:8080?x=secret',
                    'http://proxy:8080#secret', 'http://proxy:0', 'http://proxy:99999',
                    'http://proxy:\n8080', 'http://[invalid'):
            with self.subTest(url=url):
                with self.assertRaises(ValueError) as raised:
                    self.Proxy(url)
                self.assertNotIn('secret', str(raised.exception))

    def test_bytes_and_halfclose_are_forwarded_to_exact_configured_proxy(self):
        request = b'CONNECT public.example:443 HTTP/1.1\r\n\r\n'
        response = b'HTTP/1.1 200 Connection established\r\n\r\nopaque-tls-bytes'
        seen = []

        def respond(stream):
            chunks = bytearray()
            while block := stream.recv(1024):
                chunks.extend(block)
            seen.append(bytes(chunks))
            stream.sendall(response)

        connect = socket.create_connection
        with self.upstream(respond) as address:
            def dial(target, timeout):
                self.assertEqual(target, ('fixture.invalid', 8080))
                return connect(address, timeout)
            with patch('socket.create_connection', side_effect=dial), self.Proxy('http://fixture.invalid:8080') as relay:
                port = urlsplit(relay.guest_url).port
                self.assertEqual(relay._listener.getsockname(), ('127.0.0.1', port))
                with connect(('127.0.0.1', port), 3) as client:
                    client.sendall(request)
                    client.shutdown(socket.SHUT_WR)
                    actual = bytearray()
                    while block := client.recv(1024):
                        actual.extend(block)
                self.assertEqual(bytes(actual), response)
                self.assertEqual(seen, [request])
                self.assertEqual(relay.provenance['upstream_host'], 'fixture.invalid')
            self.assertFalse(relay._thread.is_alive())
            self.assertFalse(relay._workers)

    def test_close_terminates_active_connection_and_listener(self):
        accepted = threading.Event()

        def respond(stream):
            accepted.set()
            while stream.recv(1024):
                pass

        connect = socket.create_connection
        with self.upstream(respond) as address:
            with patch('socket.create_connection', side_effect=lambda target, timeout: connect(address, timeout)):
                relay = self.Proxy('http://fixture.invalid:8080', connect_timeout=1)
                with relay:
                    port = urlsplit(relay.guest_url).port
                    client = connect(('127.0.0.1', port), 3)
                    self.assertTrue(accepted.wait(2))
                with client:
                    self.assertEqual(client.recv(1), b'')
                self.assertFalse(relay._workers)
                self.assertFalse(relay._thread.is_alive())
                with self.assertRaises(OSError):
                    connect(('127.0.0.1', port), 0.2)
                relay.close()

    def test_connection_limit_closes_excess_client_without_dialing(self):
        accepted = threading.Event()
        release = threading.Event()

        def respond(stream):
            accepted.set()
            release.wait(3)

        connect = socket.create_connection
        with self.upstream(respond) as address:
            with patch('socket.create_connection', side_effect=lambda target, timeout: connect(address, timeout)) as dial:
                with self.Proxy('http://fixture.invalid:8080', max_connections=1) as relay:
                    port = urlsplit(relay.guest_url).port
                    with connect(('127.0.0.1', port), 3) as first:
                        self.assertTrue(accepted.wait(2))
                        with connect(('127.0.0.1', port), 3) as excess:
                            self.assertEqual(excess.recv(1), b'')
                        self.assertEqual(dial.call_count, 1)
                        release.set()


if __name__ == '__main__':
    unittest.main()
