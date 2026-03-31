# Shortcut Skill for OpenClaw

Manage stories on Shortcut.com kanban boards directly from your OpenClaw agent.

## What this skill does

- list active, completed, or all stories
- create stories with descriptions and types
- update story status and descriptions
- manage checklist tasks and comments
- handle webhook-driven Shortcut mentions and assignments

## Installation

This skill is already laid out as an OpenClaw skill in this repo.

### Option 1: use it from this workspace

If you're working inside this repository, no extra install step is needed. The skill files live at:

```bash
repos/clawbot-kit/skills/shortcut
```

### Option 2: install into OpenClaw's skills directory

Copy or symlink the `shortcut` folder into your OpenClaw skills path:

```bash
mkdir -p ~/.openclaw/skills
cp -R repos/clawbot-kit/skills/shortcut ~/.openclaw/skills/shortcut
```

Then restart OpenClaw if needed.

### Option 3: update from source

If you already have the skill installed elsewhere, sync it from this repo instead of fetching an old clawhub package.

## Prerequisites

- Shortcut.com account with API access
- API token from Shortcut.com (Settings → API Tokens)
- Token must have permissions for the workspace(s) you want to manage

## Configuration

1. Store your Shortcut API token:
   ```bash
   mkdir -p ~/.config/shortcut
   echo "your-token" > ~/.config/shortcut/api-token
   chmod 600 ~/.config/shortcut/api-token
   ```

2. Initialize workflow states for your workspace:
   ```bash
   scripts/shortcut-init-workflow.sh
   ```

This will auto-detect your workspace's workflow state IDs and save them to `~/.config/shortcut/workflow-states`.

## Usage

Once installed, your OpenClaw agent can handle requests like:

- "Add a story to the board: Fix login bug"
- "Show me active stories on Shortcut"
- "Mark story #38 as started"

## Scripts

The skill includes scripts for:

- listing stories
- showing story details
- creating stories
- updating stories
- managing checklist tasks
- adding, updating, and deleting comments

## License

MIT

## Author

@catwalksophie