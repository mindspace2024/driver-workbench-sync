// 司机工作台 - 数据同步服务器
// 部署后管理员和司机访问同一个地址，数据自动同步
const http = require('http');
const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, 'shared-data.json');
const PORT = process.env.PORT || 3000;

// 初始化数据文件
if (!fs.existsSync(DATA_FILE)) {
  fs.writeFileSync(DATA_FILE, JSON.stringify({
    expenses: [],
    trips: [],
    handwritten: [],
    updatedAt: new Date().toISOString()
  }));
}

function sendJSON(res, data, status = 200) {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(JSON.stringify(data));
}

function serveFile(res, filepath, contentType) {
  try {
    const content = fs.readFileSync(filepath, 'utf8');
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  } catch (e) {
    res.writeHead(404);
    res.end('Not found');
  }
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  // CORS preflight
  if (req.method === 'OPTIONS') {
    sendJSON(res, {});
    return;
  }

  // 数据 API：读取共享数据
  if (req.method === 'GET' && url.pathname === '/api/data') {
    const data = fs.readFileSync(DATA_FILE, 'utf8');
    sendJSON(res, JSON.parse(data));
    return;
  }

  // 数据 API：写入共享数据
  if (req.method === 'POST' && url.pathname === '/api/data') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const parsed = JSON.parse(body);
        parsed.updatedAt = new Date().toISOString();
        fs.writeFileSync(DATA_FILE, JSON.stringify(parsed, null, 2));
        sendJSON(res, { ok: true, updatedAt: parsed.updatedAt });
      } catch (e) {
        sendJSON(res, { error: '数据格式错误' }, 400);
      }
    });
    return;
  }

  // 静态文件
  const requestPath = url.pathname === '/' ? '/index.html' : url.pathname;
  const filePath = path.join(__dirname, requestPath);

  if (requestPath.endsWith('.html')) serveFile(res, filePath, 'text/html; charset=utf-8');
  else if (requestPath.endsWith('.js')) serveFile(res, filePath, 'application/javascript');
  else if (requestPath.endsWith('.css')) serveFile(res, filePath, 'text/css');
  else if (requestPath.endsWith('.json')) serveFile(res, filePath, 'application/json');
  else if (requestPath.endsWith('.svg')) serveFile(res, filePath, 'image/svg+xml');
  else if (requestPath.endsWith('.png')) {
    try {
      const content = fs.readFileSync(filePath);
      res.writeHead(200, { 'Content-Type': 'image/png' });
      res.end(content);
    } catch (e) { res.writeHead(404); res.end(); }
  }
  else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(PORT, () => {
  console.log(`🚗 司机工作台同步服务器已启动: http://localhost:${PORT}`);
});
