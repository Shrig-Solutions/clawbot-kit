#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
CONFIG_DIR="$SKILL_DIR/config"
CONFIG_PATH="$CONFIG_DIR/config.json"
NGROK_CONFIG="$CONFIG_DIR/ngrok-agentmail.yml"
TARGET_DATA_DIR="$SKILL_DIR/data/agentmail-webhook-viewer"

mkdir -p "$CONFIG_DIR" "$TARGET_DATA_DIR"

if [[ ! -f "$CONFIG_PATH" ]]; then
  cp "$SKILL_DIR/assets/agentmail-webhook-viewer.config.example.json" "$CONFIG_PATH"
  echo "Created $CONFIG_PATH from bundled template"
fi
if [[ ! -f "$NGROK_CONFIG" ]]; then
  cp "$SKILL_DIR/assets/ngrok-agentmail.yml.example" "$NGROK_CONFIG"
  echo "Created $NGROK_CONFIG from bundled template"
fi

chmod +x \
  "$SKILL_DIR/scripts/install_launchagent.sh" \
  "$SKILL_DIR/scripts/install_agentmail_proxy_launchagent.sh" \
  "$SKILL_DIR/scripts/install_ngrok_launchagent.sh" \
  "$SKILL_DIR/scripts/print_public_url.sh"

node --check "$SKILL_DIR/scripts/agentmail_webhook_viewer_server.mjs"
node --check "$SKILL_DIR/scripts/agentmail_proxy.mjs"

bash "$SKILL_DIR/scripts/install_launchagent.sh"
bash "$SKILL_DIR/scripts/install_agentmail_proxy_launchagent.sh"
bash "$SKILL_DIR/scripts/install_ngrok_launchagent.sh"

sleep 2

echo
echo "Config: $CONFIG_PATH"
echo "Ngrok config: $NGROK_CONFIG"
echo "Edit inboxAgentMap as needed."
echo
echo "Local viewer check:"
curl -sS -i http://127.0.0.1:8788/hooks/agentmail | sed -n '1,12p'
echo
echo "Local proxied check:"
curl -sS -i http://127.0.0.1:18801/hooks/agentmail | sed -n '1,12p'
echo
echo "Public URL:"
"$SKILL_DIR/scripts/print_public_url.sh" || true
