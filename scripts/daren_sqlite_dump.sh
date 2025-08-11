#!/usr/bin/env bash
set -euo pipefail

if [ -f "$HOME/.ghost/daren.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.ghost/daren.env"
fi

: "${DAREN_DB_PATH:?Missing DAREN_DB_PATH}"

"$(dirname "$0")/daren_ssh.sh" "sqlite3 $DAREN_DB_PATH 'SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name;'"


