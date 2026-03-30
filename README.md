# clawbot-kit

Portable Clawbot/OpenClaw skill kit.

## Included skills

- `skills/agentmail`
- `skills/shortcut`

## Install

Clone this repo, then copy or symlink the desired skill folders into your local OpenClaw skills directory.

Example:

```bash
mkdir -p ~/.openclaw/skills
cp -R skills/agentmail ~/.openclaw/skills/
cp -R skills/shortcut ~/.openclaw/skills/
```

## Notes

- Example assets are included.
- Local config, tokens, `.env`, runtime state, logs, and other machine-specific files are intentionally excluded.
