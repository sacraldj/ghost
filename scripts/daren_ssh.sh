#!/usr/bin/env bash
set -euo pipefail

# Load local secrets if present
if [ -f "$HOME/.ghost/daren.env" ]; then
  # shellcheck disable=SC1090
  source "$HOME/.ghost/daren.env"
fi

: "${DAREN_SSH_HOST:?Missing DAREN_SSH_HOST}"
: "${DAREN_SSH_USER:=root}"
: "${DAREN_SSH_PORT:=22}"
: "${DAREN_SSH_PASS:?Missing DAREN_SSH_PASS}"

exec sshpass -p "$DAREN_SSH_PASS" ssh -o StrictHostKeyChecking=no -p "$DAREN_SSH_PORT" "$DAREN_SSH_USER@$DAREN_SSH_HOST" "$@"


