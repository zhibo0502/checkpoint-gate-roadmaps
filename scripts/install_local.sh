#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST="$CODEX_HOME/skills/checkpoint-gate-roadmaps"

mkdir -p "$DEST"
rsync -a --delete \
  --exclude .git \
  --exclude __pycache__ \
  "$REPO_ROOT/" "$DEST/"

if ! diff -qr --exclude=.git "$REPO_ROOT" "$DEST" >/dev/null; then
  echo "Error: installed skill differs from repository after sync." >&2
  exit 1
fi

echo "Installed checkpoint-gate-roadmaps to $DEST"
