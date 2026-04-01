#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib/bundles.sh"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install-clawbot-bundle.sh --bundle <backend|frontend|full-stack> [options]

Options:
  --bundle NAME         Bundle to install.
  --openclaw-home PATH  Target OpenClaw home. Default: ~/.openclaw
  --copy                Copy skills into ~/.openclaw/skills
  --symlink             Symlink skills into ~/.openclaw/skills (default)
  --model NAME          Default model name to record for the bundle
  --bot NAME            Default bot name to record for the bundle
  --channel NAME        Default channel name to record for the bundle
  --list-bundles        Print supported bundles and exit
  -h, --help            Show this help text

This installer:
  - installs the selected skill bundle into ~/.openclaw/skills
  - writes bundle profile defaults under ~/.openclaw/clawbot-kit/profiles
  - creates agent manifests, prompts, and skill lists under ~/.openclaw/clawbot-kit/agents/<bundle>

The script prepares OpenClaw home structure and agent scaffolding. It does not install
the OpenClaw binary itself.

Supported platforms:
  - macOS
  - Linux (including Ubuntu)
EOF
}

detect_platform() {
  local uname_out
  uname_out="$(uname -s)"
  case "$uname_out" in
    Darwin) printf '%s\n' macos ;;
    Linux) printf '%s\n' linux ;;
    *)
      echo "Unsupported operating system: $uname_out" >&2
      echo "This installer currently supports macOS and Linux." >&2
      exit 1
      ;;
  esac
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

json_escape() {
  local value="${1//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}

write_json_array() {
  local first=1
  local item
  printf '['
  for item in "$@"; do
    if [[ $first -eq 0 ]]; then
      printf ', '
    fi
    printf '"%s"' "$(json_escape "$item")"
    first=0
  done
  printf ']'
}

install_skill() {
  local skill="$1"
  local source_dir="$REPO_ROOT/skills/$skill"
  local target_dir="$SKILLS_DIR/$skill"

  if [[ ! -d "$source_dir" ]]; then
    echo "Missing skill directory: $source_dir" >&2
    exit 1
  fi

  if [[ "$INSTALL_METHOD" == "copy" ]]; then
    rm -rf "$target_dir"
    cp -R "$source_dir" "$target_dir"
  else
    ln -sfn "$source_dir" "$target_dir"
  fi
}

write_profile() {
  local bundle="$1"
  local profile_path="$PROFILES_DIR/$bundle.env"
  local skills_csv
  skills_csv="$(paste -sd, "$TMP_DIR/$bundle.skills")"

  cat > "$profile_path" <<EOF
OPENCLAW_HOME="$OPENCLAW_HOME"
OPENCLAW_MODEL="$MODEL"
OPENCLAW_BOT="$BOT"
OPENCLAW_CHANNEL="$CHANNEL"
CLAWBOT_KIT_PLATFORM="$PLATFORM"
CLAWBOT_KIT_BUNDLE="$bundle"
CLAWBOT_KIT_SKILLS="$skills_csv"
EOF
}

write_agent_files() {
  local bundle="$1"
  local agent="$2"
  local agent_dir="$AGENTS_DIR/$bundle"
  local manifest_path="$agent_dir/$agent.json"
  local prompt_path="$agent_dir/$agent.prompt.md"
  local skills_path="$agent_dir/$agent.skills"
  local prompt
  local -a skills=()
  local skill

  mkdir -p "$agent_dir"

  while IFS= read -r skill; do
    skills+=("$skill")
  done < <(agent_skills "$bundle" "$agent")

  prompt="$(agent_prompt "$bundle" "$agent")"

  printf '%s\n' "${skills[@]}" > "$skills_path"
  printf '%s\n' "$prompt" > "$prompt_path"

  cat > "$manifest_path" <<EOF
{
  "id": "$(json_escape "$agent")",
  "bundle": "$(json_escape "$bundle")",
  "platform": "$(json_escape "$PLATFORM")",
  "role": "$(json_escape "$(agent_role "$bundle" "$agent")")",
  "model": "$(json_escape "$MODEL")",
  "bot": "$(json_escape "$BOT")",
  "channel": "$(json_escape "$CHANNEL")",
  "skills": $(write_json_array "${skills[@]}"),
  "promptFile": "$(json_escape "$prompt_path")"
}
EOF
}

write_bundle_manifest() {
  local bundle="$1"
  local manifest_path="$BUNDLES_DIR/$bundle.json"
  local -a bundle_skills_arr=()
  local -a agent_names=()
  local item

  while IFS= read -r item; do
    bundle_skills_arr+=("$item")
  done < "$TMP_DIR/$bundle.skills"

  while IFS= read -r item; do
    agent_names+=("$item")
  done < <(bundle_agents "$bundle")

  cat > "$manifest_path" <<EOF
{
  "bundle": "$(json_escape "$bundle")",
  "platform": "$(json_escape "$PLATFORM")",
  "model": "$(json_escape "$MODEL")",
  "bot": "$(json_escape "$BOT")",
  "channel": "$(json_escape "$CHANNEL")",
  "skills": $(write_json_array "${bundle_skills_arr[@]}"),
  "agents": $(write_json_array "${agent_names[@]}")
}
EOF
}

BUNDLE=""
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"
INSTALL_METHOD="symlink"
MODEL="${OPENCLAW_MODEL:-default}"
BOT="${OPENCLAW_BOT:-clawbot}"
CHANNEL="${OPENCLAW_CHANNEL:-}"
PLATFORM="$(detect_platform)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle)
      BUNDLE="${2:-}"
      shift 2
      ;;
    --openclaw-home)
      OPENCLAW_HOME="${2:-}"
      shift 2
      ;;
    --copy)
      INSTALL_METHOD="copy"
      shift
      ;;
    --symlink)
      INSTALL_METHOD="symlink"
      shift
      ;;
    --model)
      MODEL="${2:-}"
      shift 2
      ;;
    --bot)
      BOT="${2:-}"
      shift 2
      ;;
    --channel)
      CHANNEL="${2:-}"
      shift 2
      ;;
    --list-bundles)
      list_bundles
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$BUNDLE" ]]; then
  echo "--bundle is required" >&2
  usage >&2
  exit 1
fi

if ! bundle_exists "$BUNDLE"; then
  echo "Unsupported bundle: $BUNDLE" >&2
  echo "Available bundles:" >&2
  list_bundles >&2
  exit 1
fi

if [[ -z "$CHANNEL" ]]; then
  CHANNEL="$BUNDLE"
fi

require_command bash
require_command cp
require_command ln
require_command mkdir
require_command mktemp
require_command paste
require_command sed

SKILLS_DIR="$OPENCLAW_HOME/skills"
KIT_DIR="$OPENCLAW_HOME/clawbot-kit"
AGENTS_DIR="$KIT_DIR/agents"
BUNDLES_DIR="$KIT_DIR/bundles"
PROFILES_DIR="$KIT_DIR/profiles"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$SKILLS_DIR" "$AGENTS_DIR" "$BUNDLES_DIR" "$PROFILES_DIR"

bundle_skills "$BUNDLE" > "$TMP_DIR/$BUNDLE.skills"

while IFS= read -r skill; do
  install_skill "$skill"
done < "$TMP_DIR/$BUNDLE.skills"

while IFS= read -r agent; do
  write_agent_files "$BUNDLE" "$agent"
done < <(bundle_agents "$BUNDLE")

write_profile "$BUNDLE"
write_bundle_manifest "$BUNDLE"

cat <<EOF
Installed bundle: $BUNDLE
Platform: $PLATFORM
OpenClaw home: $OPENCLAW_HOME
Install method: $INSTALL_METHOD
Model: $MODEL
Bot: $BOT
Channel: $CHANNEL

Installed skills:
$(sed 's/^/- /' "$TMP_DIR/$BUNDLE.skills")

Generated files:
- $PROFILES_DIR/$BUNDLE.env
- $BUNDLES_DIR/$BUNDLE.json
- $AGENTS_DIR/$BUNDLE/

Next steps:
1. Review the generated agent prompts in $AGENTS_DIR/$BUNDLE
2. Source the profile defaults if useful: source $PROFILES_DIR/$BUNDLE.env
3. Wire these manifests into your local OpenClaw agent registration flow
EOF
