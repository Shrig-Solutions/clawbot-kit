#!/usr/bin/env bash
set -euo pipefail

OPENCLAW_INSTALL_URL="${OPENCLAW_INSTALL_URL:-https://openclaw.ai/install-cli.sh}"

usage() {
  cat <<EOF
Usage:
  bash scripts/install-openclaw-local.sh [installer flags]

Runs the official OpenClaw local-prefix installer from:
  $OPENCLAW_INSTALL_URL

Examples:
  bash scripts/install-openclaw-local.sh
  bash scripts/install-openclaw-local.sh --prefix ~/.openclaw --version latest
  bash scripts/install-openclaw-local.sh --prefix /opt/openclaw --onboard
  bash scripts/install-openclaw-local.sh --help

This is a thin wrapper around the official installer documented at:
  https://docs.openclaw.ai/install
  https://docs.openclaw.ai/install/installer
EOF
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

detect_platform() {
  local uname_out
  uname_out="$(uname -s)"
  case "$uname_out" in
    Darwin|Linux) ;;
    *)
      echo "Unsupported operating system: $uname_out" >&2
      echo "This wrapper currently supports macOS and Linux." >&2
      exit 1
      ;;
  esac
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
fi

detect_platform
require_command curl
require_command bash

echo "Running official OpenClaw local-prefix installer: $OPENCLAW_INSTALL_URL"
curl -fsSL --proto '=https' --tlsv1.2 "$OPENCLAW_INSTALL_URL" | bash -s -- "$@"
