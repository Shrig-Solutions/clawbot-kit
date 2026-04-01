#!/usr/bin/env bash
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P -- "$(dirname -- "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P -- "$(dirname -- "$SOURCE")" && pwd)"

TARGET_DIR="${HOME}/.local/bin"
TARGET_PATH="${TARGET_DIR}/clawkit"
SOURCE_PATH="${SCRIPT_DIR}/clawkit.sh"
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
FISH_PATH_LINE='fish_add_path -m $HOME/.local/bin'

detect_shell_kind() {
  case "${SHELL:-}" in
    */fish) printf '%s\n' fish ;;
    */zsh) printf '%s\n' zsh ;;
    *) printf '%s\n' bash ;;
  esac
}

detect_shell_profile() {
  local shell_kind="$1"

  if [[ "$shell_kind" == "fish" ]]; then
    printf '%s\n' "${HOME}/.config/fish/config.fish"
    return
  fi

  if [[ "$shell_kind" == "zsh" ]]; then
    if [[ -n "${ZDOTDIR:-}" ]]; then
      if [[ -f "${ZDOTDIR}/.zshrc" || ! -e "${ZDOTDIR}/.zshrc" ]]; then
        printf '%s\n' "${ZDOTDIR}/.zshrc"
        return
      fi
      if [[ -f "${ZDOTDIR}/.zprofile" ]]; then
        printf '%s\n' "${ZDOTDIR}/.zprofile"
        return
      fi
    fi
    if [[ -f "${HOME}/.zshrc" || ! -e "${HOME}/.zshrc" ]]; then
      printf '%s\n' "${HOME}/.zshrc"
      return
    fi
    printf '%s\n' "${HOME}/.zprofile"
    return
  fi

  if [[ -f "${HOME}/.bashrc" || ! -e "${HOME}/.bashrc" ]]; then
    printf '%s\n' "${HOME}/.bashrc"
    return
  fi
  if [[ -f "${HOME}/.bash_profile" ]]; then
    printf '%s\n' "${HOME}/.bash_profile"
    return
  fi
  printf '%s\n' "${HOME}/.profile"
}

ensure_path_line() {
  local profile_path="$1"
  local shell_kind="$2"
  local line_to_add="$PATH_LINE"

  if [[ "$shell_kind" == "fish" ]]; then
    line_to_add="$FISH_PATH_LINE"
  fi

  mkdir -p "$(dirname "$profile_path")"
  touch "$profile_path"

  if grep -Fqx "$line_to_add" "$profile_path"; then
    return
  fi

  {
    printf '\n'
    printf '%s\n' "$line_to_add"
  } >> "$profile_path"
}

mkdir -p "$TARGET_DIR"
ln -sfn "$SOURCE_PATH" "$TARGET_PATH"
chmod +x "$SOURCE_PATH"

SHELL_KIND="$(detect_shell_kind)"
PROFILE_PATH="$(detect_shell_profile "$SHELL_KIND")"
ensure_path_line "$PROFILE_PATH" "$SHELL_KIND"

cat <<EOF
Installed clawkit command:
  $TARGET_PATH

Updated shell profile:
  $PROFILE_PATH

Detected shell:
  $SHELL_KIND

Reload your shell and run:
  clawkit --help
EOF
