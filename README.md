# clawbot-kit

Portable Clawbot/OpenClaw skill kit.

## Included skills

- `skills/agentmail` — email workflows and inbox-triggered agents
- `skills/shortcut` — Shortcut story and task management

## Install

Clone this repo, then copy or symlink the desired skill folders into your local OpenClaw skills directory.

Example:

```bash
mkdir -p ~/.openclaw/skills
cp -R skills/agentmail ~/.openclaw/skills/
cp -R skills/shortcut ~/.openclaw/skills/
```

## Setup overview

Each skill has its own README with setup steps. In general, you will need to:

- add the API token or key for the service
- copy the example config into your local config path
- fill in agent/inbox/workspace mappings
- run the bootstrap or init script for webhook-enabled skills

## Ngrok / EC2 hosting

Some skills use ngrok plus a small proxy/webhook setup when the public endpoint is hosted on EC2 or another remote machine.

Typical flow:

- install the ngrok LaunchAgent or service for the skill
- configure the shared public host or tunnel target
- keep local webhook and proxy services running
- verify the public route before enabling webhook delivery

Relevant skill files:

- `skills/agentmail/scripts/install_ngrok_launchagent.sh`
- `skills/shortcut/scripts/install_ngrok_launchagent.sh`
- `skills/agentmail/assets/ngrok-agentmail.yml.example`
- `skills/shortcut/assets/ngrok-shortcut.yml.example`

## Notes

- Example assets are included.
- Local config, tokens, `.env`, runtime state, logs, and other machine-specific files are intentionally excluded.
