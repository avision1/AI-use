#!/usr/bin/env python3
"""Binary School local server. Python 3.8+, standard library only."""
import argparse
import http.server
import json
from pathlib import Path
import sys
import threading
import urllib.parse
import webbrowser

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'site'

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def do_GET(self):
        try:
            self._serve(False)
        except (BrokenPipeError, ConnectionResetError):
            pass  # A cancelled browser download is not a server failure.

    def do_HEAD(self):
        self._serve(True)

    def _serve(self, head):
        # Serve only this folder's public site, never launchers, backups or arbitrary paths.
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        if path == '/__binary_school__/health':
            payload = json.dumps({'app':'Binary School', 'edition':'localhost', 'version':'1.2.0'}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            if not head:
                self.wfile.write(payload)
            return
        if '\\' in path or '\x00' in path or any(part in ('.', '..') for part in path.split('/')):
            self.send_error(403, 'Path not allowed')
            return
        target = (SITE / path.lstrip('/')).resolve()
        if target != SITE and SITE not in target.parents:
            self.send_error(403, 'Path not allowed')
            return
        if target.is_dir() and not (target / 'index.html').is_file():
            self.send_error(403, 'Directory listing disabled')
            return
        if head:
            super().do_HEAD()
        else:
            super().do_GET()

    def guess_type(self, path):
        suffix = Path(path).suffix.lower()
        if suffix in ('.c', '.s', '.py', '.sh', '.bat', '.txt'):
            return 'text/plain; charset=utf-8'
        if suffix == '.js':
            return 'text/javascript; charset=utf-8'
        if suffix == '.json':
            return 'application/json'
        return super().guess_type(path)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        super().end_headers()


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run Binary School on your own laptop. No packages to install.')
    parser.add_argument('--port', type=int, default=8765, help='Local port (default: 8765). Use the same port to retain browser progress.')
    parser.add_argument('--no-browser', action='store_true', help='Print the URL without opening a browser')
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('Port must be between 1 and 65535.')
    if sys.version_info < (3, 8):
        parser.error('Python 3.8 or newer is required.')
    if not (SITE / 'index.html').is_file():
        parser.error('site/index.html is missing. Extract the entire ZIP before starting.')
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as error:
        print('Could not start the local server: {}'.format(error), file=sys.stderr)
        print('Close any previous Binary School server and try again, or use --port 8766.', file=sys.stderr)
        print('Changing the port creates a separate browser progress store; import a backup if needed.', file=sys.stderr)
        return 1
    server.daemon_threads = True
    url = 'http://localhost:{}/'.format(args.port)
    print('\nBinary School — localhost edition\n')
    print('Open: ' + url)
    print('Only this laptop can connect. Keep this window open.')
    print('Press Ctrl+C to stop. YouTube and external references require internet.\n', flush=True)
    if not args.no_browser:
        def open_browser():
            try:
                if not webbrowser.open(url):
                    print('Open the URL above in your browser manually.', flush=True)
            except Exception:
                print('Open the URL above in your browser manually.', flush=True)
        threading.Thread(target=open_browser, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nBinary School stopped.')
    finally:
        server.server_close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
