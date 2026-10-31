#!/usr/bin/env bash
set -u
APP="$HOME/SmartTV"
[ -d "$APP/.git" ] || exit 0
cd "$APP" || exit 0
timeout 20 git fetch origin main >/tmp/smarttv-update.log 2>&1 || exit 0
[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ] || exit 0
rm -rf "$HOME/.local/share/smarttv/rollback"
mkdir -p "$HOME/.local/share/smarttv/rollback"
git archive HEAD | tar -x -C "$HOME/.local/share/smarttv/rollback" || exit 0
git reset --hard origin/main >>/tmp/smarttv-update.log 2>&1 || exit 0
docker compose up -d --build >>/tmp/smarttv-update.log 2>&1 || exit 0
"$APP/.venv/bin/pip" install -q -r "$APP/host-agent/requirements.txt" >>/tmp/smarttv-update.log 2>&1 || true
exit 0
