# clawbot-kit

Portable Clawbot/OpenClaw skill kit.

## Included skills

- `skills/agentmail` — email workflows and inbox-triggered agents
- `skills/shortcut` — Shortcut story and task management
- `skills/git-commit` — commit helper workflow
- `skills/git-essentials` — core Git workflow helpers

## Install

Clone this repo, then copy or symlink the desired skill folders into your local OpenClaw skills directory.

Example:

```bash
mkdir -p ~/.openclaw/skills
cp -R skills/agentmail ~/.openclaw/skills/
cp -R skills/shortcut ~/.openclaw/skills/
cp -R skills/git-commit ~/.openclaw/skills/
cp -R skills/git-essentials ~/.openclaw/skills/
```

## Setup overview

Each skill has its own README with setup steps. In general, you will need to:

- add the API token or key for the service
- copy the example config into your local config path
- fill in agent/inbox/workspace mappings
- run the bootstrap or init script for webhook-enabled skills

## Notes

- Example assets are included.
- Local config, tokens, `.env`, runtime state, logs, and other machine-specific files are intentionally excluded.
