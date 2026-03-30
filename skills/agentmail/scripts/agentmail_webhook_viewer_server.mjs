#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const SCRIPT_DIR = path.dirname(new URL(import.meta.url).pathname);
const SKILL_DIR = path.resolve(SCRIPT_DIR, '..');
const CONFIG_DIR = path.join(SKILL_DIR, 'config');
const DATA_DIR = path.join(SKILL_DIR, 'data', 'agentmail-webhook-viewer');
const CONFIG_PATH = process.env.AGENTMAIL_WEBHOOK_VIEWER_CONFIG || path.join(CONFIG_DIR, 'config.json');
const EVENTS_FILE = path.join(DATA_DIR, 'events.json');

function loadJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function ensureConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    throw new Error(`Missing config: ${CONFIG_PATH}. Create it from assets/agentmail-webhook-viewer.config.example.json.`);
  }
  return loadJson(CONFIG_PATH);
}

fs.mkdirSync(CONFIG_DIR, { recursive: true });
fs.mkdirSync(DATA_DIR, { recursive: true });

const config = ensureConfig();
const PORT = Number(process.env.PORT || config.port || 8788);
const HOST = process.env.HOST || config.host || '127.0.0.1';
const MAX_EVENTS = Number(process.env.MAX_EVENTS || config.maxEvents || 200);
const OPENCLAW_BIN = process.env.OPENCLAW_BIN || config.openclaw?.binary || '/opt/homebrew/bin/openclaw';

function loadEvents() {
  try {
    return JSON.parse(fs.readFileSync(EVENTS_FILE, 'utf8'));
  } catch {
    return [];
  }
}

function saveEvents(events) {
  fs.writeFileSync(EVENTS_FILE, JSON.stringify(events.slice(-MAX_EVENTS), null, 2));
}

function collectBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function safeParseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function resolveAgentForInbox(inboxId) {
  const inboxMap = config.inboxAgentMap || {};
  return inboxMap[(inboxId || '').toLowerCase()] || null;
}

function formatAgentMessage({ inboxId, from, subject, messageText }) {
  const fromLine = Array.isArray(from)
    ? from.map((entry) => entry?.email || entry?.name || '').filter(Boolean).join(', ')
    : (from?.email || from?.name || 'unknown');
  return [
    `📬 AgentMail received for ${inboxId || 'unknown inbox'}`,
    `From: ${fromLine || 'unknown'}`,
    `Subject: ${subject || '(no subject)'}`,
    '',
    'Message:',
    (messageText || '').trim() || '(no body)',
    '',
    'Action:',
    '- Send an ACK reply immediately from this inbox.',
    '- Then perform the requested task if any.',
  ].join('\n');
}

function triggerAgent(agentId, message) {
  return new Promise((resolve) => {
    const args = [
      'agent',
      '--agent', agentId,
      '--message', message,
      '--thinking', config.openclaw?.thinking || 'low',
      '--timeout', String(config.openclaw?.timeoutSeconds || 600),
    ];
    const env = {
      ...process.env,
      PATH: `/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin${process.env.PATH ? `:${process.env.PATH}` : ''}`,
    };

    try {
      const child = spawn(OPENCLAW_BIN, args, {
        stdio: 'ignore',
        env,
        detached: true,
      });
      child.unref();
      resolve({ ok: true, queued: true, code: 0, stdout: '', stderr: '' });
    } catch (err) {
      resolve({ ok: false, queued: false, code: null, stdout: '', stderr: String(err?.message || err) });
    }
  });
}

function extractSummary(parsedBody) {
  const eventType = parsedBody?.event_type || parsedBody?.eventType || 'unknown';
  const message = parsedBody?.message || parsedBody?.data?.message || parsedBody?.body?.message || {};
  const inboxId = (message?.inbox_id || message?.inboxId || '').toLowerCase();
  const from = message?.from ?? message?.from_ ?? null;
  const subject = message?.subject || null;
  const messageField = message?.text || message?.preview || message?.extracted_text || null;
  const mappedAgent = resolveAgentForInbox(inboxId);
  const isRealInbound = eventType === 'message.received' && inboxId && from && (subject || messageField);

  return {
    eventType,
    inboxId,
    agentToTrigger: isRealInbound ? mappedAgent : null,
    from,
    subject,
    message: messageField,
    shouldTrigger: Boolean(isRealInbound && mappedAgent),
  };
}

function formatTimestamp(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return {
    iso: d.toISOString(),
    local: d.toLocaleString('en-US', {
      timeZone: 'Asia/Katmandu',
      year: 'numeric', month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: true,
      timeZoneName: 'short',
    }),
  };
}

function viewerLabelForEvent(event) {
  if (event.shouldTrigger && event.agentTriggered) {
    return `Triggers agent: ${event.agentTriggered}`;
  }
  if (event.eventType !== 'message.received') {
    return `Skipped: non-inbound event (${event.eventType || 'unknown'})`;
  }
  if (event.inboxId && !resolveAgentForInbox(event.inboxId)) {
    return `Skipped: inbox not mapped (${event.inboxId})`;
  }
  return 'Skipped: not triggerable';
}

function formatViewerEvent(event) {
  return {
    at: formatTimestamp(event.timestamp),
    eventType: event.eventType || 'unknown',
    inbox: event.inboxId || '(unknown inbox)',
    from: Array.isArray(event.from)
      ? event.from.map((entry) => entry?.email || entry?.name || '').filter(Boolean).join(', ') || 'unknown'
      : (event.from?.email || event.from?.name || 'unknown'),
    subject: event.subject || '(no subject)',
    preview: event.message || '(no message text)',
    trigger: {
      decision: viewerLabelForEvent(event),
      shouldTrigger: Boolean(event.shouldTrigger),
      agent: event.agentTriggered || null,
      ok: event.triggerOk ?? null,
      code: event.triggerCode ?? null,
      note: event.triggerStderr || null,
    },
    request: {
      method: event.method,
      path: event.path,
      bodyLength: event.bodyLength,
    },
  };
}

function buildViewerResponse(url) {
  const events = loadEvents();
  const recent = events.slice(-10).reverse().map(formatViewerEvent);
  return {
    ok: true,
    service: 'agentmail-webhook-viewer',
    status: 'listening',
    endpoint: '/hooks/agentmail',
    method: 'GET',
    message: 'POST AgentMail webhooks to this URL. This GET view shows the most recent events first.',
    count: events.length,
    recent,
    query: Object.fromEntries(url.searchParams.entries()),
  };
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

  if (req.method === 'GET' && (url.pathname === '/hooks/agentmail' || url.pathname === '/hooks/agentmail/')) {
    res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(buildViewerResponse(url), null, 2));
    return;
  }

  if ((url.pathname === '/agentmail/raw' || url.pathname === '/hooks/agentmail') && ['POST', 'PUT', 'PATCH'].includes(req.method || '')) {
    const bodyBuffer = await collectBody(req);
    const bodyText = bodyBuffer.toString('utf8');
    const parsedBody = safeParseJson(bodyText);
    const summary = extractSummary(parsedBody);
    let triggerResult = { ok: false, code: null, stdout: '', stderr: 'skipped' };
    if (summary.shouldTrigger) {
      const agentMessage = formatAgentMessage({
        inboxId: summary.inboxId,
        from: summary.from,
        subject: summary.subject,
        messageText: summary.message,
      });
      triggerResult = await triggerAgent(summary.agentToTrigger, agentMessage);
    }

    const event = {
      timestamp: new Date().toISOString(),
      method: req.method,
      path: url.pathname + url.search,
      bodyLength: bodyBuffer.length,
      ...summary,
      agentTriggered: summary.shouldTrigger ? summary.agentToTrigger : null,
      triggerOk: summary.shouldTrigger ? triggerResult.ok : null,
      triggerCode: summary.shouldTrigger ? triggerResult.code : null,
      triggerStderr: summary.shouldTrigger ? (triggerResult.ok ? null : triggerResult.stderr?.slice(0, 600) || null) : 'skipped-non-inbound-or-unmapped',
      body: parsedBody ?? bodyText,
    };

    const events = loadEvents();
    events.push(event);
    saveEvents(events);

    res.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ ok: true, stored: true, triggered: summary.agentToTrigger, count: events.length }, null, 2));
    return;
  }

  res.writeHead(404, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify({ ok: false, error: 'not-found' }, null, 2));
});

server.listen(PORT, HOST, () => {
  console.log(`AgentMail webhook viewer listening on http://${HOST}:${PORT}`);
  console.log(`Using config: ${CONFIG_PATH}`);
  console.log('Capture endpoint: /agentmail/raw');
  console.log('JSON events: /agentmail/raw/events');
});
