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

## Install OpenClaw

This repo now includes thin wrappers around the official OpenClaw installer scripts documented here:

- [Install](https://docs.openclaw.ai/install)
- [Installer internals](https://docs.openclaw.ai/install/installer)

Default machine install on macOS/Linux:

```bash
bash scripts/install-openclaw.sh
```

Skip onboarding:

```bash
bash scripts/install-openclaw.sh --no-onboard
```

Local-prefix install under `~/.openclaw`:

```bash
bash scripts/install-openclaw-local.sh
```

Custom local prefix:

```bash
bash scripts/install-openclaw-local.sh --prefix /opt/openclaw --version latest
```

These wrappers call the official hosted installer scripts from `openclaw.ai`, so the target machine needs internet access.

## Run skill scripts from repo root

You can run skill-local scripts through a single dynamic launcher from the repo root:

```bash
python3 scripts/skill.py <skill> [script] [args...]
bash scripts/skill.sh <skill> [script] [args...]
```

Examples:

```bash
python3 scripts/skill.py agentmail
python3 scripts/skill.py agentmail send_email.py --agent main --to someone@example.com --subject Hello --text Test
bash scripts/skill.sh shortcut bootstrap.sh
```

If the script name is omitted, the launcher tries `skills/<skill>/scripts/setup_skill.py`.

## Attach a skill to one agent

You can also add a skill to one generated agent and immediately run that skill's setup flow:

```bash
python3 scripts/clawkit.py agent <agent_name> skill <skill_name>
bash scripts/clawkit.sh agent <agent_name> skill <skill_name>
```

Examples:

```bash
python3 scripts/clawkit.py agent backend skill agentmail
python3 scripts/clawkit.py agent backend skill agentmail --bundle full-stack
python3 scripts/clawkit.py agent backend skill agentmail -- --help
```

That command:

- installs the skill into `~/.openclaw/skills`
- updates only the targeted agent manifest and `.skills` file
- refreshes the bundle-level skill union in the bundle manifest and profile
- runs the skill's `setup_skill.py` when that script exists

## Create a separate OpenClaw agent for one skill

`clawkit` can also create a real isolated OpenClaw agent for a specific skill. This follows the documented OpenClaw CLI flow for `openclaw agents add` and uses a dedicated workspace so the skill applies only to that agent.

Relevant OpenClaw docs:

- [CLI reference: agents](https://docs.openclaw.ai/cli#agents)
- [Agents command page](https://docs.openclaw.ai/cli/agents)
- [Multi-agent routing](https://docs.openclaw.ai/multi-agent)
- [Skills location and precedence](https://docs.openclaw.ai/tools/creating-skills)

Commands:

```bash
python3 scripts/clawkit.py create-agent <agent_name> skill <skill_name>
bash scripts/clawkit.sh create-agent <agent_name> skill <skill_name>
python3 scripts/clawkit.py list-agents
bash scripts/clawkit.sh list-agents
```

Examples:

```bash
python3 scripts/clawkit.py create-agent backend-mail skill agentmail --model gpt-5.2
python3 scripts/clawkit.py create-agent ops-shortcut skill shortcut --bind telegram:ops
python3 scripts/clawkit.py create-agent backend-mail skill agentmail -- --help
```

That command:

- ensures the skill is available in shared `~/.openclaw/skills`
- creates a dedicated agent workspace under `~/.openclaw/clawbot-kit/workspaces/<agent_name>`
- places the selected skill under that workspace's local `skills/` directory
- runs `openclaw agents add <agent_name> --workspace <dir> --agent-dir <dir> --non-interactive`
- optionally passes `--model` and repeatable `--bind` arguments through to OpenClaw
- optionally runs the skill's `setup_skill.py` after the agent is created

To list current agents:

```bash
python3 scripts/clawkit.py list-agents
bash scripts/clawkit.sh list-agents
```

When `openclaw` is available on PATH, this runs:

```bash
openclaw agents list --bindings
```

If the OpenClaw CLI is unavailable, `clawkit` falls back to local bundle manifests under `~/.openclaw/clawbot-kit/agents/`.

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
