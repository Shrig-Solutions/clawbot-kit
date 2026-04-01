---
name: shortcut
description: Manage stories on Shortcut.com kanban boards. Use when creating, updating, listing, commenting on, or otherwise acting on Shortcut stories/tasks, including webhook-driven event handling such as assignment or @mention triggers from Shortcut comments. Supports creating stories with descriptions and types (feature/bug/chore), updating story status, listing active/completed stories, checklist task management, and comments. Defaults to the Fishtechy workflow unless explicitly overridden.
---

# Shortcut Kanban Integration

Manage tasks and stories on Shortcut boards via API.

## Attach To An Agent

To add this skill to a specific generated agent:

```bash
python3 scripts/clawkit.py skill add shortcut to <agent_name>
```

Example:

```bash
python3 scripts/clawkit.py skill add shortcut to backend --bundle full-stack
```

To create a separate OpenClaw agent dedicated to this skill:

```bash
python3 scripts/clawkit.py skill new-agent shortcut as shortcut-bot
```

## Event-driven behavior

When invoked from a Shortcut webhook or a pasted Shortcut event:

1. Extract the referenced story id from the event payload/message.
2. Read the story first with `scripts/shortcut-show-story.sh <story-id>` to get current description, tasks, and recent comments.
3. Use the triggering comment text as the primary instruction when present.
4. Execute the requested action when the skill supports it.
5. If the request is a lightweight acknowledgment (`reply`, `ack`, `react here`, `reply here`, `confirm`) and true reactions are not supported, post a short comment acknowledgment instead of stalling.
6. If the request asks for an external action the skill does not perform directly (for example email), perform the closest supported Shortcut-side acknowledgment and clearly report any remaining limitation.

Default acknowledgment text for simple test prompts:

- `Ack — received.`

Do not ask unnecessary clarification questions for obvious webhook test commands.

## Prerequisites

- Configure a Shortcut API token via:
  - environment variable: `SHORTCUT_API_TOKEN`, or
  - file: `~/.config/shortcut/api-token`
- Default workflow: `Fishtechy`
- Workflow config file: `~/.config/shortcut/workflow-states`

## Setup

1. Store the token:
   ```bash
   mkdir -p ~/.config/shortcut
   echo "your-token" > ~/.config/shortcut/api-token
   chmod 600 ~/.config/shortcut/api-token
   ```
2. Initialize workflow states for the default Fishtechy workflow:
   ```bash
   scripts/shortcut-init-workflow.sh
   ```
3. Bootstrap the webhook side if you want inbound Shortcut triggers:
   ```bash
   bash scripts/bootstrap.sh
   ```

Read `references/LOCAL-WEBHOOK.md` when working on the webhook receiver, LaunchAgents, or public webhook URL.
The public Shortcut path uses the shared host via `/shortcut/webhook`.

## Local webhook config

Main config:
- `~/.openclaw/skills/shortcut/config/config.json`

Ngrok config:
- `~/.openclaw/skills/shortcut/config/ngrok-shortcut.yml`

The webhook config maps Shortcut mentions/assignments to OpenClaw agents through `agents.*`.

## Available Operations

### List stories

```bash
scripts/shortcut-list-stories.sh [--active|--completed|--all] [--json]
```

### Show story details

```bash
scripts/shortcut-show-story.sh <story-id>
```

### Create story

Creates stories in the configured workflow's default todo state. With the default config, that means **Fishtechy → To do**.

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

The update script reads `~/.config/shortcut/workflow-states` and maps status changes to the configured workflow.

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

- Scripts use `SHORTCUT_API_TOKEN` first, then fall back to `~/.config/shortcut/api-token`.
- The shared default workflow is now `Fishtechy`.
- Re-run `scripts/shortcut-init-workflow.sh` after switching tokens/workspaces so state IDs stay correct.
