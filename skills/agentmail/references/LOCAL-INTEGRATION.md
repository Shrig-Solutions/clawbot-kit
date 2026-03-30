# Local AgentMail Integration

Use this when the goal is not just sending email, but handling **incoming AgentMail email that should wake an OpenClaw agent automatically**.

## Current architecture

Flow:

1. Sender emails an AgentMail inbox like `nirman@agentmail.to`
2. AgentMail posts a webhook to the public URL:
   - `https://<public-host>/hooks/agentmail`
3. The AgentMail-only proxy forwards `/hooks/agentmail` to:
   - `http://127.0.0.1:8788/hooks/agentmail`
4. The skill-managed webhook service stores the webhook event
5. If the event is a real inbound `message.received` for a configured inbox, the service runs:
   - `openclaw agent --agent <mapped-agent> --message <formatted-email-prompt>`
6. The target agent decides what to do and may reply via AgentMail API scripts

## Skill-managed files

Main files live under the skill:
- `~/.openclaw/skills/agentmail/scripts/agentmail_webhook_viewer_server.mjs`
- `~/.openclaw/skills/agentmail/scripts/install_launchagent.sh`
- `~/.openclaw/skills/agentmail/scripts/agentmail_proxy.mjs`
- `~/.openclaw/skills/agentmail/scripts/install_agentmail_proxy_launchagent.sh`
- `~/.openclaw/skills/agentmail/scripts/bootstrap.sh`
- `~/.openclaw/skills/agentmail/config/config.json`
- `~/.openclaw/skills/agentmail/data/agentmail-webhook-viewer/events.json`

## Required config

The webhook service reads:
- `~/.openclaw/skills/agentmail/config/config.json`

Important field:
- `inboxAgentMap`

Example:

```json
{
  "inboxAgentMap": {
    "nirman@agentmail.to": "nirman"
  }
}
```

## Local and public health checks

Local viewer:

```bash
curl -i http://127.0.0.1:8788/hooks/agentmail
```

Through AgentMail proxy:

```bash
curl -i http://127.0.0.1:18800/hooks/agentmail
```

Public:

```bash
curl -i https://<public-host>/hooks/agentmail
```

Expected result for all:
- `200 OK`
- JSON with `service: "agentmail-webhook-viewer"`

## LaunchAgents

Webhook viewer label:
- `com.openclaw.agentmail-webhook-viewer`

AgentMail proxy label:
- `com.openclaw.gateway-proxy`

Logs:
- `~/.openclaw/logs/agentmail-webhook-viewer.log`
- `~/.openclaw/logs/agentmail-webhook-viewer.err.log`
- `~/.openclaw/logs/gateway-proxy.log`
- `~/.openclaw/logs/gateway-proxy.err.log`

## Bootstrap

Run one command:

```bash
bash ~/.openclaw/skills/agentmail/scripts/bootstrap.sh
```

Optional public-host check:

```bash
bash ~/.openclaw/skills/agentmail/scripts/bootstrap.sh hornblendic-sariah-poetically.ngrok-free.dev
```

That bootstrap:
- ensures config exists
- syntax-checks the viewer and proxy scripts
- installs/restarts the webhook viewer LaunchAgent
- installs/restarts the AgentMail proxy LaunchAgent
- checks local viewer and proxied routes
- optionally checks the public route

## What this hook is for

Keep `/hooks/agentmail` if inbound email should automatically wake agents.

You do **not** need it for outbound-only email sending.
