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

mkdir -p "$TARGET_DIR"
ln -sfn "$SOURCE_PATH" "$TARGET_PATH"
chmod +x "$SOURCE_PATH"

cat <<EOF
Installed clawkit command:
  $TARGET_PATH

If ~/.local/bin is not on your PATH yet, add this to your shell profile:
  export PATH="\$HOME/.local/bin:\$PATH"

Then reload your shell and run:
  clawkit --help
EOF
