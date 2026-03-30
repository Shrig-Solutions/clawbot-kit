#!/usr/bin/env node
import http from 'node:http';

const PORT = 18801;
const OPENCLAW_TARGET = { host: '127.0.0.1', port: 18789 };
const AGENTMAIL_VIEWER_TARGET = { host: '127.0.0.1', port: 8788 };

function pickTarget(req) {
  const url = req.url || '';
  if (url.startsWith('/agentmail/webhook')) return AGENTMAIL_VIEWER_TARGET;
  return OPENCLAW_TARGET;
}

const server = http.createServer((req, res) => {

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
  console.log(`AgentMail proxy listening on http://127.0.0.1:${PORT}`);
  console.log('Routes: /agentmail/webhook -> 8788, everything else -> 18789');
});
