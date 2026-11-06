#!/usr/bin/env python3
"""Expose only the inherited HTTP proxy to a QEMU user-network guest.

The relay transports bytes unchanged to one configured proxy. It never resolves
HTTP destinations, changes TLS validation, or records request/response bytes.
"""
import select
import socket
import threading
import time
from urllib.parse import urlsplit


class GuestProxy:
    def __init__(self, url, *, max_connections=16, connect_timeout=10, idle_timeout=120):
        if (type(max_connections) is not int or not 1 <= max_connections <= 64
                or not 0 < connect_timeout <= 60 or not 0 < idle_timeout <= 600):
            raise ValueError('Proxy relay resource limits are invalid')
        self.guest_url = ''
        self.provenance = {'mode': 'none'}
        self._listener = self._thread = None
        self._closed = threading.Event()
        self._lock = threading.Lock()
        self._sockets, self._workers = set(), set()
        self._slots = threading.BoundedSemaphore(max_connections)
        self._connect_timeout, self._idle_timeout = connect_timeout, idle_timeout
        self._target = None
        if not url:
            return
        try:
            parsed = urlsplit(url)
            host = parsed.hostname
            port = 80 if parsed.port is None else parsed.port
            valid = (parsed.scheme == 'http' and host and 1 <= port <= 65535 and parsed.username is None
                     and parsed.password is None and parsed.path in ('', '/')
                     and not parsed.query and not parsed.fragment
                     and not any(c.isspace() or ord(c) < 32 for c in url))
        except (ValueError, TypeError):
            valid = False
        if not valid:
            raise ValueError('A plain HTTP proxy URL without credentials, path or query is required')
        self._target = (host, port)
        self.provenance = {'mode': 'loopback' if host in ('localhost', '127.0.0.1') else 'relay',
                           'upstream_host': host, 'upstream_port': port}
        if self.provenance['mode'] == 'loopback':
            self.guest_url = f'http://10.0.2.2:{port}'

    def __enter__(self):
        if self._closed.is_set() or self._thread is not None:
            raise ValueError('Proxy relay cannot be reopened')
        if self.provenance['mode'] == 'relay':
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                listener.bind(('127.0.0.1', 0))
                listener.listen(16)
                listener.settimeout(0.2)
                self._listener = listener
                self.guest_url = f'http://10.0.2.2:{listener.getsockname()[1]}'
                self._thread = threading.Thread(target=self._serve, daemon=True)
                self._thread.start()
            except BaseException:
                listener.close()
                raise
        return self

    def _serve(self):
        while not self._closed.is_set():
            try:
                client, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            if self._closed.is_set() or not self._slots.acquire(blocking=False):
                client.close()
                continue
            worker = threading.Thread(target=self._forward, args=(client,), daemon=True)
            with self._lock:
                self._sockets.add(client)
                self._workers.add(worker)
            worker.start()

    def _forward(self, client):
        upstream = None
        try:
            if self._closed.is_set():
                return
            upstream = socket.create_connection(self._target, timeout=self._connect_timeout)
            with self._lock:
                self._sockets.add(upstream)
            for stream in (client, upstream):
                stream.settimeout(self._connect_timeout)
            readers = [client, upstream]
            deadline = time.monotonic() + self._idle_timeout
            while readers and not self._closed.is_set():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                ready, _, _ = select.select(readers, [], [], min(0.2, remaining))
                for source in ready:
                    destination = upstream if source is client else client
                    data = source.recv(65536)
                    if not data:
                        readers.remove(source)
                        destination.shutdown(socket.SHUT_WR)
                    else:
                        destination.sendall(data)
                        deadline = time.monotonic() + self._idle_timeout
        except (OSError, ValueError):
            pass
        finally:
            with self._lock:
                for stream in (client, upstream):
                    if stream is not None:
                        self._sockets.discard(stream)
                        stream.close()
                self._workers.discard(threading.current_thread())
            self._slots.release()

    def close(self):
        self._closed.set()
        if self._listener is not None:
            self._listener.close()
        if self._thread is not None:
            self._thread.join(timeout=1)
        with self._lock:
            for stream in self._sockets:
                try:
                    stream.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            workers = list(self._workers)
        deadline = time.monotonic() + self._connect_timeout + 1
        for worker in workers:
            worker.join(timeout=max(0, deadline - time.monotonic()))

    def __exit__(self, *exception):
        self.close()
