#!/bin/bash
# Create a new Shortcut story
# Usage: ./shortcut-create-story.sh "Story name" [--description "text"] [--type feature|bug|chore]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/shortcut-common.sh"

TOKEN="$(shortcut_require_token)"
shortcut_load_workflow_config
BASE_URL="https://api.app.shortcut.com/api/v3"

# Args
STORY_NAME="${1:-}"
DESCRIPTION=""
STORY_TYPE="feature"
WORKFLOW_STATE_ID="${SHORTCUT_STATE_TODO}"

if [ -z "$STORY_NAME" ]; then
  echo "Usage: $0 \"Story name\" [--description \"text\"] [--type feature|bug|chore]" >&2
  exit 1
fi
shift

# Parse optional args
while [[ $# -gt 0 ]]; do
  case $1 in
    --description)
      DESCRIPTION="$2"
      shift 2
      ;;
    --type)
      STORY_TYPE="$2"
      shift 2
      ;;
    --state-id)
      WORKFLOW_STATE_ID="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Build JSON payload
PAYLOAD=$(jq -n \
  --arg name "$STORY_NAME" \
  --arg type "$STORY_TYPE" \
  --arg desc "$DESCRIPTION" \
  --argjson workflow_state_id "$WORKFLOW_STATE_ID" \
  '{
    name: $name,
    story_type: $type,
    workflow_state_id: $workflow_state_id
  } + (if $desc != "" then {description: $desc} else {} end)')

# Create story
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Shortcut-Token: $TOKEN" \
  -d "$PAYLOAD" \
  "$BASE_URL/stories")

# Output
STORY_ID=$(echo "$RESPONSE" | jq -r '.id')
STORY_URL=$(echo "$RESPONSE" | jq -r '.app_url')

if [ "$STORY_ID" != "null" ]; then
  echo "✅ Created story #$STORY_ID: $STORY_NAME"
  echo "   Workflow: ${SHORTCUT_WORKFLOW_NAME}"
  echo "   $STORY_URL"
else
  echo "❌ Failed to create story" >&2
  echo "$RESPONSE" | jq . >&2
  exit 1
fi
