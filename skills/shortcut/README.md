# Shortcut Skill for OpenClaw

Manage stories on Shortcut.com kanban boards directly from your OpenClaw agent.

## What this skill does

- list active, completed, or all stories
- create stories with descriptions and types
- update story status and descriptions
- manage checklist tasks and comments
- handle webhook-driven Shortcut mentions and assignments

## Prerequisites

Before you start, make sure you have:

- a Shortcut.com account with API access
- an OpenClaw workspace already set up
- a shell with `bash` available
- permission to edit files under `~/.openclaw/skills`

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

## Setup

### 1) Add your Shortcut API token

Store your API token in the standard location:

```bash
mkdir -p ~/.config/shortcut
printf 'your-token\n' > ~/.config/shortcut/api-token
chmod 600 ~/.config/shortcut/api-token
```

You can also use `SHORTCUT_API_TOKEN` in the environment.

### 2) Initialize workflow state mapping

Set up the workflow state IDs for your workspace:

```bash
scripts/shortcut-init-workflow.sh
```

This auto-detects your workspace's workflow state IDs and saves them to:

```bash
~/.config/shortcut/workflow-states
```

Run it again whenever you switch tokens or workspaces.

### 3) Optional webhook/bootstrap setup

If you want inbound Shortcut mentions and assignments to wake OpenClaw, bootstrap the webhook side too:

```bash
bash scripts/bootstrap.sh
```

The local webhook config lives at:

```bash
~/.openclaw/skills/shortcut/config/config.json
```

### What bootstrap covers

`bash scripts/bootstrap.sh` sets up the local webhook receiver and proxy pieces.

### What you still need to do

You still need to configure Shortcut to send webhooks to your public URL so mentions and assignments can reach OpenClaw.

## Usage

Once installed, your OpenClaw agent can handle requests like:

- "Add a story to the board: Fix login bug"
- "Show me active stories on Shortcut"
- "Mark story #38 as started"
- "Add a checklist item to that story"

## Available operations

### List stories

```bash
scripts/shortcut-list-stories.sh [--active|--completed|--all] [--json]
```

### Show story details

```bash
scripts/shortcut-show-story.sh <story-id>
```

### Create story

```bash
scripts/shortcut-create-story.sh "Story name" [--description "text"] [--type feature|bug|chore]
```

Optional override:

```bash
scripts/shortcut-create-story.sh "Story name" --state-id 12345
```

### Update story

```bash
scripts/shortcut-update-story.sh <story-id> [--complete|--todo|--in-progress|--blocked] [--description "new text"]
```

### Checklist tasks

```bash
scripts/shortcut-create-task.sh <story-id> "task description"
scripts/shortcut-update-task.sh <story-id> <task-id> [--complete|--incomplete]
scripts/shortcut-edit-task.sh <story-id> <task-id> "new description"
scripts/shortcut-delete-task.sh <story-id> <task-id>
```

### Comments

```bash
scripts/shortcut-add-comment.sh <story-id> "comment text"
scripts/shortcut-update-comment.sh <story-id> <comment-id> "new text"
scripts/shortcut-delete-comment.sh <story-id> <comment-id>
```

## Notes

- Scripts use `SHORTCUT_API_TOKEN` first, then fall back to `~/.config/shortcut/api-token`
- The shared default workflow is `Fishtechy`
- Re-run `scripts/shortcut-init-workflow.sh` after switching tokens/workspaces so state IDs stay correct
- Read `references/LOCAL-WEBHOOK.md` when working on the webhook receiver, LaunchAgents, or public webhook URL

## License

MIT

## Author

@catwalksophie