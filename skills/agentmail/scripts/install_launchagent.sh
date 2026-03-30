#!/usr/bin/env bash
set -euo pipefail
LABEL="com.openclaw.agentmail-webhook-viewer"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
WORKDIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
NODE_BIN="$(command -v node)"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.openclaw/logs"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
      <string>${NODE_BIN}</string>
      <string>${WORKDIR}/scripts/agentmail_webhook_viewer_server.mjs</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${WORKDIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/.openclaw/logs/agentmail-webhook-viewer.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/.openclaw/logs/agentmail-webhook-viewer.err.log</string>
  </dict>
</plist>
PLIST
launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/${LABEL}"
echo "Installed ${LABEL}: $PLIST"
