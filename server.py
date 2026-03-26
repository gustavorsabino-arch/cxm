#!/usr/bin/env python3
"""
CXM Dashboard — local dev server
  • Serves static files on http://localhost:8080
  • Proxies POST /v1/messages → https://api.anthropic.com/v1/messages
    (bypasses browser CORS restriction for direct Anthropic API calls)

Usage:
    python3 server.py
Then open:
    http://localhost:8080/CXM_Financial_Dashboard_V2.html
"""
import http.server, urllib.request, urllib.error, os, sys

PORT = 8080

CORS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': (
        'Content-Type, x-api-key, anthropic-version, '
        'anthropic-beta, anthropic-dangerous-direct-browser-calls'
    ),
}

PROXY_HEADERS = ('content-type', 'x-api-key', 'anthropic-version',
                 'anthropic-beta', 'anthropic-dangerous-direct-browser-calls')


class Handler(http.server.SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        if self.path.startswith('/v1/'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)

            target = 'https://api.anthropic.com' + self.path
            req = urllib.request.Request(target, data=body, method='POST')
            for h in PROXY_HEADERS:
                val = self.headers.get(h)
                if val:
                    req.add_header(h, val)

            try:
                with urllib.request.urlopen(req) as r:
                    data = r.read()
                    self._proxy_respond(r.status, data)
            except urllib.error.HTTPError as e:
                self._proxy_respond(e.code, e.read())
            except Exception as e:
                self._proxy_respond(502, str(e).encode())
        else:
            self.send_response(405)
            self.end_headers()

    def _proxy_respond(self, status, data):
        self.send_response(status)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        msg = fmt % args
        prefix = '[proxy]' if '/v1/' in msg else '[serve]'
        print(prefix, msg)


if __name__ == '__main__':
    # Serve files from the same directory as this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
    try:
        with http.server.HTTPServer(('', PORT), Handler) as srv:
            print(f'CXM Dashboard server running on http://localhost:{PORT}')
            print(f'Open: http://localhost:{PORT}/CXM_Financial_Dashboard_V2.html')
            print('Press Ctrl+C to stop.\n')
            srv.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
    except OSError as e:
        print(f'Error: {e}')
        print(f'Port {PORT} may be in use. Try: python3 server.py (after killing the old process)')
        sys.exit(1)
