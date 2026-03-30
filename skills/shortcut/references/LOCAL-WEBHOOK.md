# Local Shortcut Webhook

This skill ships its own local webhook receiver. Public exposure uses the shared OpenClaw/ngrok host through the shared proxy on port `18800`.

## Main files

- `~/.openclaw/skills/shortcut/scripts/shortcut_webhook_server.mjs`
- `~/.openclaw/skills/shortcut/scripts/install_webhook_launchagent.sh`
- `~/.openclaw/skills/shortcut/scripts/print_public_url.sh`
- `~/.openclaw/skills/shortcut/scripts/bootstrap.sh`
- `~/.openclaw/skills/shortcut/config/config.json`

## Config

Webhook config:
- `~/.openclaw/skills/shortcut/config/config.json`

## Bootstrap

```bash
bash ~/.openclaw/skills/shortcut/scripts/bootstrap.sh
```

That bootstrap:
- ensures config exists
- syntax-checks the webhook server
- installs/restarts the local webhook LaunchAgent
- checks the local webhook endpoint
- prints the public webhook URL on the shared host

## Endpoints

Local:
- `http://127.0.0.1:8787/shortcut/webhook`

Public:
- `https://<shared-public-host>/shortcut/webhook`
- printed by `scripts/print_public_url.sh`

## LaunchAgents

- `com.openclaw.shortcut-hooks`
- shared proxy is provided by the AgentMail skill via `com.openclaw.gateway-proxy`
