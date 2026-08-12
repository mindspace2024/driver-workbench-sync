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
DATA_FILE = os.path.join(os.path.dirname(__file__), 'shared-data.json')

# 种子数据：每次部署/重启后自动恢复，不再丢 7 月
SEED_DATA = {
    "expenses": [
        {"id":"jul_0","date":"2026-06-30","type":"备用金","amount":3835.1,"description":"上月结转余额","advanceReceived":True,"advanceReceivedDate":"2026-06-30","advanceReceivedMethod":"微信转账","advanceReceivedAmount":3835.1,"status":"approved","reviewNote":"历史数据导入","submittedBy":"driver","role":"driver","createdAt":"2026-06-30T00:00:00.000Z"},
        {"id":"jul_1","date":"2026-07-01","type":"过路费","amount":100,"description":"上海到崇明岛过路费","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-01T00:00:00.000Z"},
        {"id":"jul_2","date":"2026-07-03","type":"加油/充电","amount":320,"status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-03T00:00:00.000Z"},
        {"id":"jul_3","date":"2026-07-03","type":"停车费","amount":20,"description":"虹桥T2停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-03T00:00:00.000Z"},
        {"id":"jul_4","date":"2026-07-04","type":"停车费","amount":10,"description":"虹桥T2停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-04T00:00:00.000Z"},
        {"id":"jul_5","date":"2026-07-04","type":"停车费","amount":10,"description":"太仓路停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-04T00:00:00.000Z"},
        {"id":"jul_6","date":"2026-07-05","type":"停车费","amount":4,"description":"金桥大厦停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-05T00:00:00.000Z"},
        {"id":"jul_7","date":"2026-07-06","type":"加油/充电","amount":315,"status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-06T00:00:00.000Z"},
        {"id":"jul_8","date":"2026-07-06","type":"停车费","amount":10,"description":"虹桥T2停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-06T00:00:00.000Z"},
        {"id":"jul_9","date":"2026-07-06","type":"洗车","amount":60,"description":"洗车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-06T00:00:00.000Z"},
        {"id":"jul_10","date":"2026-07-09","type":"停车费","amount":12,"description":"上海站停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-09T00:00:00.000Z"},
        {"id":"jul_11","date":"2026-07-11","type":"停车费","amount":10,"description":"虹桥T2停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-11T00:00:00.000Z"},
        {"id":"jul_12","date":"2026-07-11","type":"加油/充电","amount":310,"status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-11T00:00:00.000Z"},
        {"id":"jul_13","date":"2026-07-11","type":"其他","amount":44,"description":"备用水","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-11T00:00:00.000Z"},
        {"id":"jul_14","date":"2026-07-12","type":"停车费","amount":8,"description":"仁恒海上源停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-12T00:00:00.000Z"},
        {"id":"jul_15","date":"2026-07-17","type":"停车费","amount":10,"description":"虹桥T2停车","status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-17T00:00:00.000Z"},
        {"id":"jul_16","date":"2026-07-17","type":"加油/充电","amount":335,"status":"approved","advanceDeducted":True,"submittedBy":"driver","role":"driver","createdAt":"2026-07-17T00:00:00.000Z"},
    ],
    "trips": [],
    "handwritten": [],
    "updatedAt": ""
}

# 初始化数据文件（种子数据确保部署后自动恢复）
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump(SEED_DATA, f, ensure_ascii=False)
else:
    with open(DATA_FILE, 'r') as f:
        current = json.load(f)
    if len(current.get('expenses', [])) == 0:
        with open(DATA_FILE, 'w') as f:
            json.dump(SEED_DATA, f, ensure_ascii=False)


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
