#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
CONFIG_DIR="$SKILL_DIR/config"
DATA_DIR="$SKILL_DIR/data/shortcut-webhook"
CONFIG_PATH="$CONFIG_DIR/config.json"
NGROK_CONFIG="$CONFIG_DIR/ngrok-shortcut.yml"
mkdir -p "$CONFIG_DIR" "$DATA_DIR"
if [[ ! -f "$CONFIG_PATH" ]]; then
  cp "$SKILL_DIR/assets/shortcut-webhook.config.example.json" "$CONFIG_PATH"
  echo "Created $CONFIG_PATH from bundled template"
fi
if [[ ! -f "$NGROK_CONFIG" ]]; then
  cp "$SKILL_DIR/assets/ngrok-shortcut.yml.example" "$NGROK_CONFIG"
  echo "Created $NGROK_CONFIG from bundled template"
fi
chmod +x "$SKILL_DIR/scripts/install_webhook_launchagent.sh" "$SKILL_DIR/scripts/install_shortcut_proxy_launchagent.sh" "$SKILL_DIR/scripts/install_ngrok_launchagent.sh" "$SKILL_DIR/scripts/print_public_url.sh"
node --check "$SKILL_DIR/scripts/shortcut_webhook_server.mjs"
node --check "$SKILL_DIR/scripts/shortcut_proxy.mjs"
bash "$SKILL_DIR/scripts/install_webhook_launchagent.sh"
bash "$SKILL_DIR/scripts/install_shortcut_proxy_launchagent.sh"
bash "$SKILL_DIR/scripts/install_ngrok_launchagent.sh"
sleep 2
echo
echo "Config: $CONFIG_PATH"
echo "Ngrok config: $NGROK_CONFIG"
echo "Edit webhookSecret and agent mappings as needed."
echo
echo "Local check:"
curl -sS -i http://127.0.0.1:8787/shortcut/webhook | sed -n '1,12p'
echo
echo "Local proxied check:"
curl -sS -i http://127.0.0.1:18802/shortcut/webhook | sed -n '1,12p'
echo
echo "Public URL:"
"$SKILL_DIR/scripts/print_public_url.sh" || true
