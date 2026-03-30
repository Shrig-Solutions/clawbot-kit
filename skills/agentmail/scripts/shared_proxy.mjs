#!/usr/bin/env node
import http from 'node:http';

const PORT = 18800;
const OPENCLAW_TARGET = { host: '127.0.0.1', port: 18789 };
const SHORTCUT_TARGET = { host: '127.0.0.1', port: 8787 };
const AGENTMAIL_VIEWER_TARGET = { host: '127.0.0.1', port: 8788 };

function pickTarget(req) {
  const url = req.url || '';
  if (url.startsWith('/shortcut/webhook')) return SHORTCUT_TARGET;
  if (url.startsWith('/agentmail/raw')) return AGENTMAIL_VIEWER_TARGET;
  if (url.startsWith('/hooks/agentmail')) return AGENTMAIL_VIEWER_TARGET;
  return OPENCLAW_TARGET;
}

const server = http.createServer((req, res) => {
  const url = req.url || '';

  if (req.method === 'GET' && url === '/hooks/agentmail/events') {
    res.writeHead(302, { location: '/agentmail/raw/events' });
    res.end();
    return;
  }
  if (req.method === 'GET' && url === '/hooks/agentmail/events.json') {
    res.writeHead(302, { location: '/agentmail/raw/events.json' });
    res.end();
    return;
  }

  const target = pickTarget(req);
  const proxyReq = http.request({
    host: target.host,
    port: target.port,
    method: req.method,
    path: req.url,
    headers: req.headers,
  }, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    res.writeHead(502, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: false, error: 'proxy-error', detail: String(err.message || err) }));
  });

  req.pipe(proxyReq);
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`OpenClaw shared proxy listening on http://127.0.0.1:${PORT}`);
  console.log('Routes: /shortcut/webhook -> 8787, /agentmail/raw* -> 8788, /hooks/agentmail -> 8788, everything else -> 18789');
});
