#!/bin/bash
# Update a Shortcut story (move state, mark complete, add description)
# Usage: ./shortcut-update-story.sh <story-id> [options]
#   --complete         Mark as complete
#   --todo             Move to To do
#   --in-progress      Move to InProgress
#   --blocked          Move to Hold/Blocked
#   --description "text"  Update description

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/shortcut-common.sh"

TOKEN="$(shortcut_require_token)"
shortcut_load_workflow_config
BASE_URL="https://api.app.shortcut.com/api/v3"

STORY_ID="${1:-}"
if [ -z "$STORY_ID" ]; then
  echo "Usage: $0 <story-id> [options]" >&2
  exit 1
fi
shift

# Build update payload
UPDATES=()

while [[ $# -gt 0 ]]; do
  case $1 in
    --complete)
      UPDATES+=("\"workflow_state_id\": $SHORTCUT_STATE_DONE")
      shift
      ;;
    --todo)
      UPDATES+=("\"workflow_state_id\": $SHORTCUT_STATE_TODO")
      shift
      ;;
    --in-progress)
      UPDATES+=("\"workflow_state_id\": $SHORTCUT_STATE_IN_PROGRESS")
      shift
      ;;
    --blocked)
      UPDATES+=("\"workflow_state_id\": $SHORTCUT_STATE_BLOCKED")
      shift
      ;;
    --description)
      UPDATES+=("\"description\": $(jq -Rn --arg v "$2" '$v')")
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [ ${#UPDATES[@]} -eq 0 ]; then
  echo "No updates specified" >&2
  exit 1
fi

# Join updates with commas
PAYLOAD="{$(IFS=,; echo "${UPDATES[*]}")}"

# Update story
RESPONSE=$(curl -s -X PUT \
  -H "Content-Type: application/json" \
  -H "Shortcut-Token: $TOKEN" \
  -d "$PAYLOAD" \
  "$BASE_URL/stories/$STORY_ID")

# Output
STORY_NAME=$(echo "$RESPONSE" | jq -r '.name')
if [ "$STORY_NAME" != "null" ]; then
  echo "✅ Updated story #$STORY_ID: $STORY_NAME"
  echo "   Workflow: ${SHORTCUT_WORKFLOW_NAME}"
else
  echo "❌ Failed to update story" >&2
  echo "$RESPONSE" | jq . >&2
  exit 1
fi
