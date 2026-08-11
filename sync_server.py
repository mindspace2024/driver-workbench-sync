#!/usr/bin/env python3
"""司机工作台 - 数据同步服务器
部署后管理员和司机访问同一个地址，数据自动同步
"""

import http.server
import json
import os
import sys
from urllib.parse import urlparse

PORT = int(os.environ.get('PORT', 8080))
# Use Render persistent directory to survive deploys
DATA_DIR = os.environ.get('RENDER_DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, 'shared-data.json')

# 初始化数据文件
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({
            'expenses': [],
            'trips': [],
            'handwritten': [],
            'updatedAt': ''
        }, f)


class SyncHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/data':
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            self._send_json(data)
            return

        # Static files
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/data':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                data['updatedAt'] = self._now()
                with open(DATA_FILE, 'w') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._send_json({'ok': True, 'updatedAt': data['updatedAt']})
            except Exception as e:
                self._send_json({'error': str(e)}, 400)
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    @staticmethod
    def _now():
        from datetime import datetime, timezone, timedelta
        return datetime.now(timezone(timedelta(hours=8))).isoformat()

    def log_message(self, format, *args):
        if '/api/' in str(args[0]):
            sys.stderr.write("[API] %s\n" % (args[0]))


if __name__ == '__main__':
    print(f'🚗 司机工作台同步服务器已启动: http://localhost:{PORT}')
    print(f'   数据文件: {DATA_FILE}')
    print(f'   按 Ctrl+C 停止')
    httpd = http.server.HTTPServer(('0.0.0.0', PORT), SyncHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')
        httpd.server_close()
