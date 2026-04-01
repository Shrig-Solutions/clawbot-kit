# clawbot-kit

Portable Clawbot/OpenClaw skill kit.

## Included skills

- `skills/agentmail` — email workflows and inbox-triggered agents
- `skills/shortcut` — Shortcut story and task management
- `skills/nodejs-nestjs-backend` — Node.js and NestJS backend development guidance
- `skills/frontend-react-nextjs` — frontend development guidance for HTML, CSS, Tailwind, React, and Next.js
- `skills/git-commit` — commit helper workflow
- `skills/git-essentials` — core Git workflow helpers

## Install

Clone this repo, then copy or symlink the desired skill folders into your local OpenClaw skills directory.

Example:

```bash
mkdir -p ~/.openclaw/skills
cp -R skills/agentmail ~/.openclaw/skills/
cp -R skills/shortcut ~/.openclaw/skills/
cp -R skills/nodejs-nestjs-backend ~/.openclaw/skills/
cp -R skills/frontend-react-nextjs ~/.openclaw/skills/
cp -R skills/git-commit ~/.openclaw/skills/
cp -R skills/git-essentials ~/.openclaw/skills/
```

## Setup overview

Each skill has its own README with setup steps. In general, you will need to:

- add the API token or key for the service
- copy the example config into your local config path
- fill in agent/inbox/workspace mappings
- run the bootstrap or init script for webhook-enabled skills

## Bundle installer

This repo also ships a bundle installer for role-based Clawbot setups.

The bundle installer is designed to run on:

- macOS
- Linux
- Ubuntu

Use it to install common skills plus role-specific skills into `~/.openclaw`, and to scaffold agent manifests/prompts for bundles such as:

- `backend`
- `frontend`
- `full-stack`

Example:

```bash
bash scripts/install-clawbot-bundle.sh --bundle full-stack --model default --bot clawbot --channel engineering
bash scripts/install-full-stack-bundle.sh --model default --bot clawbot --channel engineering
```

That script:

- installs shared skills like `agentmail`, `shortcut`, `git-essentials`, and `git-commit`
- adds role skills such as `nodejs-nestjs-backend` and `frontend-react-nextjs`
- writes bundle defaults to `~/.openclaw/clawbot-kit/profiles/<bundle>.env`
- generates agent prompts, skill lists, and JSON manifests under `~/.openclaw/clawbot-kit/agents/<bundle>/`
- records the detected platform in the generated profile and manifests

The generated full-stack bundle includes:

- `main` with common + backend + frontend skills
- `backend` with common + backend skills
- `frontend` with common + frontend skills

You can list supported bundles with:

```bash
bash scripts/install-clawbot-bundle.sh --list-bundles
```

Shortcut wrappers are also available:

```bash
bash scripts/install-backend-bundle.sh
bash scripts/install-frontend-bundle.sh
bash scripts/install-full-stack-bundle.sh
```

Platform note:

- the bundle installer scripts are cross-platform for macOS and Linux
- some existing webhook/bootstrap helpers inside individual skills still rely on platform-specific service managers such as LaunchAgents, so those runtime helpers will need a Linux-specific follow-up if you want the same background-service automation there

## Notes

- Example assets are included.
- Local config, tokens, `.env`, runtime state, logs, and other machine-specific files are intentionally excluded.
