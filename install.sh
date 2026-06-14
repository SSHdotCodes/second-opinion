#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${SECOND_OPINION_BASE_URL:-https://second-opinion.ssh.codes}"
INSTALL_DIR="${SECOND_OPINION_BIN_DIR:-$HOME/.local/bin}"
BIN_PATH="$INSTALL_DIR/second-opinion"
FREEDOMCLAUDE_BASE_URL="${FREEDOMCLAUDE_BASE_URL:-https://ssh.codes/freedomclaude}"
FREEDOMCLAUDE_BASE_URL="${FREEDOMCLAUDE_BASE_URL%/}"

show_help() {
  cat <<'EOF'
Second Opinion installer

Usage:
  curl -fsSL https://second-opinion.ssh.codes/install.sh | bash
  curl -fsSL https://second-opinion.ssh.codes/install.sh | bash -s -- --agent codex --yes

Installer environment:
  SECOND_OPINION_BASE_URL   Override download host.
  SECOND_OPINION_BIN_DIR    Override CLI install directory. Defaults to ~/.local/bin.
  FREEDOMCLAUDE_BASE_URL    Override FreedomClaude download host.
  SECOND_OPINION_SKIP_FREEDOMCLAUDE=1
                             Skip the bundled FreedomClaude install.

All arguments are passed to: second-opinion install
Use --cli-only to install the CLI without adding agent skills.
Use --skip-freedomclaude to skip FreedomClaude.

Already installed?
  second-opinion update
EOF
}

cli_only=false
skip_freedomclaude="${SECOND_OPINION_SKIP_FREEDOMCLAUDE:-}"
for arg in "$@"; do
  case "$arg" in
    -h|--help)
      show_help
      exit 0
      ;;
    --cli-only)
      cli_only=true
      ;;
    --skip-freedomclaude)
      skip_freedomclaude=1
      ;;
  esac
done

mkdir -p "$INSTALL_DIR"
tmp_file="$(mktemp)"
cleanup() {
  rm -f "$tmp_file"
}
trap cleanup EXIT

download() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$BASE_URL/bin/second-opinion" -o "$tmp_file"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$tmp_file" "$BASE_URL/bin/second-opinion"
  else
    echo "error: install requires curl or wget" >&2
    exit 1
  fi
}

download
chmod 0755 "$tmp_file"
mv "$tmp_file" "$BIN_PATH"
trap - EXIT

echo "Installed Second Opinion CLI to $BIN_PATH"

case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *)
    echo "Note: $INSTALL_DIR is not on PATH. Add this to your shell profile:"
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    ;;
esac

if [ "$cli_only" = true ]; then
  exit 0
fi

install_freedomclaude() {
  if [ -n "$skip_freedomclaude" ]; then
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    echo "Warning: curl is unavailable; skipping FreedomClaude install." >&2
    return 0
  fi

  echo "Installing FreedomClaude for Claude Code terminal-mode delegation..."
  if ! curl -fsSL "$FREEDOMCLAUDE_BASE_URL/install.sh" | sh; then
    echo "Warning: FreedomClaude install failed. Claude delegation will need freedomclaude on PATH." >&2
  fi
}

install_freedomclaude

args=()
for arg in "$@"; do
  [ "$arg" = "--cli-only" ] && continue
  [ "$arg" = "--skip-freedomclaude" ] && continue
  args+=("$arg")
done

if [ "${#args[@]}" -eq 0 ] && [ -r /dev/tty ]; then
  "$BIN_PATH" install < /dev/tty
else
  "$BIN_PATH" install "${args[@]}"
fi
