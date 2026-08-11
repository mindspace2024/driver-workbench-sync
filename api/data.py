from http.server import BaseHTTPRequestHandler
import json, os

DATA_FILE = '/tmp/shared-data.json'

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        data = {'expenses': [], 'trips': [], 'handwritten': [], 'updatedAt': ''}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
        self._json(data)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else b'{}'
        data = json.loads(body)
        data['updatedAt'] = '2026-08-10T00:00:00+08:00'
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        self._json({'ok': True, 'updatedAt': data['updatedAt']})

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False)
        self.send_response(status)
        self._cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
