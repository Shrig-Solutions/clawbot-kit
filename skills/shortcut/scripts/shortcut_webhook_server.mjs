#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';

const SCRIPT_DIR = path.dirname(new URL(import.meta.url).pathname);
const SKILL_DIR = path.resolve(SCRIPT_DIR, '..');
const CONFIG_DIR = path.join(SKILL_DIR, 'config');
const DATA_DIR = path.join(SKILL_DIR, 'data', 'shortcut-webhook');
const CONFIG_PATH = process.env.SHORTCUT_WEBHOOK_CONFIG || path.join(CONFIG_DIR, 'config.json');
const STATE_PATH = path.join(DATA_DIR, 'state.json');

function loadJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function ensureConfig() {
  if (!fs.existsSync(CONFIG_PATH)) throw new Error(`Missing config: ${CONFIG_PATH}. Create it from assets/shortcut-webhook.config.example.json.`);
  return loadJson(CONFIG_PATH);
}
function loadState() {
  if (!fs.existsSync(STATE_PATH)) return { seen: {}, recent: [] };
  try {
    const state = loadJson(STATE_PATH);
    return { seen: state?.seen || {}, recent: Array.isArray(state?.recent) ? state.recent : [] };
  } catch { return { seen: {}, recent: [] }; }
}
function saveState(state) { fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2)); }
function timingSafeEqualHex(a, b) {
  try { const aa = Buffer.from(a || '', 'hex'); const bb = Buffer.from(b || '', 'hex'); return aa.length === bb.length && crypto.timingSafeEqual(aa, bb); } catch { return false; }
}
function verifySignature(rawBody, secret, header) {
  if (!secret) return true; if (!header) return false;
  const expected = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  return timingSafeEqualHex(expected, String(header || '').trim());
}
function normalizeText(value) { return String(value || '').toLowerCase(); }
function getAgents(config) { return Object.entries(config.agents || {}); }
function findReference(refs, entityType, id) { return (refs || []).find((ref) => ref?.entity_type === entityType && String(ref?.id) === String(id)); }
function getStoryAction(actions) { return (actions || []).find((a) => a?.entity_type === 'story'); }
function getCommentAction(actions) { return (actions || []).find((a) => a?.entity_type === 'comment' || a?.entity_type === 'story-comment'); }
function storyUrl(storyId) { return storyId ? `https://app.shortcut.com/desktop/story/${storyId}` : ''; }
function getStoryContext(payload) {
  const refs = payload.references || [];
  const storyAction = getStoryAction(payload.actions || []);
  const referencedStory = refs.find((ref) => ref?.entity_type === 'story');
  const storyId = referencedStory?.id || storyAction?.id || payload.primary_id || null;
  const storyName = referencedStory?.name || storyAction?.name || `Story ${storyId}`;
  return { storyId, storyName, storyAction };
}
function aliasesForAgent(agentConfig) { return (agentConfig?.aliases || []).map((x) => normalizeText(x)); }
function ownerMatchesAgent(refs, ownerId, agentConfig) {
  const map = agentConfig?.shortcutOwners || {};
  if ((map.memberIds || []).map(String).includes(String(ownerId))) return true;
  const member = findReference(refs, 'member', ownerId);
  const names = (map.memberNames || []).map(normalizeText);
  if (member?.name && names.includes(normalizeText(member.name))) return true;
  if (member?.mention_name && names.includes(normalizeText(member.mention_name))) return true;
  return false;
}
function detectCommentMentions(config, text) {
  const lower = normalizeText(text);
  return getAgents(config).filter(([, agentConfig]) => aliasesForAgent(agentConfig).some((alias) => lower.includes(alias))).map(([agentKey]) => agentKey);
}
function detectAssignmentTargets(config, payload) {
  const refs = payload.references || [];
  const action = getStoryAction(payload.actions || []);
  const adds = action?.changes?.owner_ids?.adds || [];
  return getAgents(config).filter(([, agentConfig]) => adds.some((ownerId) => ownerMatchesAgent(refs, ownerId, agentConfig))).map(([agentKey]) => agentKey);
}
function buildAgentMessage({ trigger, agentKey, payload }) {
  const { storyId, storyName } = getStoryContext(payload);
  const comment = getCommentAction(payload.actions || []);
  const commentText = comment?.text || comment?.changes?.text?.new || '';
  const actor = findReference(payload.references || [], 'member', payload.member_id)?.name || payload.member_id || 'Unknown actor';
  const lines = [`Shortcut webhook trigger for ${agentKey}.`, `Trigger: ${trigger}`, `Story: ${storyName} (#${storyId})`, `Actor: ${actor}`];
  if (commentText) { lines.push('', 'Comment:', commentText.slice(0, 4000)); }
  const url = storyUrl(storyId); if (url) lines.push('', `Shortcut URL: ${url}`);
  lines.push('', 'Action: use the installed Shortcut skill now. Inspect the referenced Shortcut story/comment, decide what the comment is asking for, and do the requested Shortcut-side action when supported. For obvious test commands like ack/reply/react/confirm, do not ask unnecessary clarification questions; use the best supported acknowledgment (for example a short Shortcut comment) if direct reactions are unavailable.');
  return lines.join('\n');
}
function dedupeKey(payload, agentKey, trigger) {
  const comment = getCommentAction(payload.actions || []);
  const { storyId } = getStoryContext(payload);
  return [payload.id || 'unknown', agentKey, trigger, comment?.id || '', storyId || payload.primary_id || ''].join(':');
}
function shouldSkip(state, key, ttlSeconds) { const now = Math.floor(Date.now() / 1000); const seenAt = state.seen[key]; return typeof seenAt === 'number' && (now - seenAt) < ttlSeconds; }
function touchState(state, key, config) {
  const now = Math.floor(Date.now() / 1000); state.seen[key] = now; const ttl = config.dedupe?.ttlSeconds || 21600;
  for (const [k, ts] of Object.entries(state.seen)) if ((now - ts) > ttl) delete state.seen[k];
  const maxKeys = config.dedupe?.maxKeys || 500; state.seen = Object.fromEntries(Object.entries(state.seen).sort((a, b) => b[1] - a[1]).slice(0, maxKeys));
}
function triggerAgent(config, agentKey, message) {
  const agentConfig = config.agents?.[agentKey] || {};
  const agentId = agentConfig.openclawAgentId || agentKey;
  const openclawBin = config.openclaw?.binary || '/opt/homebrew/bin/openclaw';
  const args = ['agent', '--agent', agentId, '--message', message, '--thinking', config.openclaw?.thinking || 'low', '--timeout', String(config.openclaw?.timeoutSeconds || 600)];
  const env = { ...process.env, PATH: `/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin${process.env.PATH ? `:${process.env.PATH}` : ''}` };
  return new Promise((resolve) => {
    try {
      const child = spawn(openclawBin, args, { cwd: config.openclaw?.workingDirectory || process.cwd(), stdio: 'ignore', env, detached: true });
      child.unref(); resolve({ queued: true, code: 0, agentId, openclawBin });
    } catch (error) { resolve({ queued: false, code: null, agentId, openclawBin, stderr: String(error?.message || error) }); }
  });
}
function summarizeRawPayload(payload) {
  const comment = getCommentAction(payload?.actions || []); const story = getStoryAction(payload?.actions || []);
  return { id: payload?.id ?? null, primary_id: payload?.primary_id ?? null, member_id: payload?.member_id ?? null, comment_text: comment?.text ?? comment?.changes?.text?.new ?? null, story_action_id: story?.id ?? null, story_action_name: story?.name ?? null };
}
function recordRecentEvent(state, summary) { const recent = Array.isArray(state.recent) ? state.recent : []; recent.unshift({ at: new Date().toISOString(), ...summary }); state.recent = recent.slice(0, 20); }
function formatTimestamp(value) { if (!value) return null; const d = new Date(value); if (Number.isNaN(d.getTime())) return value; return { iso: d.toISOString(), local: d.toLocaleString('en-US', { timeZone: 'Asia/Katmandu', year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true, timeZoneName: 'short' }) }; }
function formatRecentShortcutEvent(item) { return { at: formatTimestamp(item.at), story: { id: item.primaryId, name: item.storyName || null, commentId: item.commentId || null }, triggerSummary: (item.triggersPlanned || []).length ? `Matched ${(item.triggersPlanned || []).length} trigger(s)` : 'No agent trigger matched', results: item.results || [], raw: item.raw }; }
function buildHealthResponse(req, state) { return { ok: true, service: 'shortcut-webhook', status: 'listening', endpoint: '/shortcut/webhook', method: req.method, message: req.url === '/shortcut/webhook' ? 'Webhook endpoint is live. Send a signed POST to this URL.' : 'Unknown path. Use /shortcut/webhook with POST.', recent: (state.recent || []).slice(0, 10).map(formatRecentShortcutEvent) }; }
async function planTriggers(config, payload) {
  const triggers = [];
  for (const agentKey of detectAssignmentTargets(config, payload)) triggers.push({ agentKey, trigger: 'assignment' });
  const comment = getCommentAction(payload.actions || []); const commentText = comment?.text || comment?.changes?.text?.new || '';
  for (const agentKey of detectCommentMentions(config, commentText)) triggers.push({ agentKey, trigger: 'comment-mention' });
  const seen = new Set(); return triggers.filter((t) => { const key = `${t.agentKey}:${t.trigger}`; if (seen.has(key)) return false; seen.add(key); return true; });
}
async function handlePayload(rawBody, config) {
  const payload = JSON.parse(rawBody.toString('utf8')); const state = loadState(); const plans = await planTriggers(config, payload); const results = []; const { storyId, storyName, storyAction } = getStoryContext(payload); const comment = getCommentAction(payload.actions || []);
  for (const plan of plans) {
    const key = dedupeKey(payload, plan.agentKey, plan.trigger);
    if (shouldSkip(state, key, config.dedupe?.ttlSeconds || 21600)) { results.push({ ...plan, skipped: true, reason: 'duplicate' }); continue; }
    const message = buildAgentMessage({ ...plan, payload }); const triggerResult = await triggerAgent(config, plan.agentKey, message); touchState(state, key, config); results.push({ ...plan, skipped: false, openclaw: triggerResult });
  }
  recordRecentEvent(state, { eventId: payload.id || null, primaryId: storyId || payload.primary_id || storyAction?.id || null, storyName: storyName || null, commentId: comment?.id || null, triggersPlanned: plans, results, raw: summarizeRawPayload(payload) });
  saveState(state); return { ok: true, eventId: payload.id, results };
}
fs.mkdirSync(CONFIG_DIR, { recursive: true }); fs.mkdirSync(DATA_DIR, { recursive: true });
const config = ensureConfig(); const port = Number(process.env.PORT || config.port || 8787);
const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/shortcut/webhook') { const state = loadState(); res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(buildHealthResponse(req, state), null, 2)); return; }
  if (req.url !== '/shortcut/webhook') { const state = loadState(); res.writeHead(404, { 'content-type': 'application/json' }); res.end(JSON.stringify(buildHealthResponse(req, state), null, 2)); return; }
  if (req.method !== 'POST') { const state = loadState(); res.writeHead(405, { 'content-type': 'application/json' }); res.end(JSON.stringify({ ...buildHealthResponse(req, state), ok: false, error: 'method-not-allowed', allowedMethods: ['POST'] }, null, 2)); return; }
  const chunks = []; req.on('data', (chunk) => chunks.push(chunk)); req.on('end', async () => {
    const rawBody = Buffer.concat(chunks); const signature = req.headers['payload-signature'];
    try { if (!verifySignature(rawBody, config.webhookSecret, String(signature || ''))) { res.writeHead(401, { 'content-type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'bad-signature' })); return; }
      const result = await handlePayload(rawBody, config); res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(result, null, 2));
    } catch (error) { res.writeHead(500, { 'content-type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: String(error?.message || error) }, null, 2)); }
  });
});
server.listen(port, '127.0.0.1', () => { console.log(`Shortcut webhook listening on http://127.0.0.1:${port}/shortcut/webhook`); console.log(`Using config: ${CONFIG_PATH}`); });
