#!/usr/bin/env bash
set -u
APP="$HOME/SmartTV";cd "$APP"||exit 0
timeout 20 git fetch origin main >/tmp/smarttv-update.log 2>&1||exit 0
[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]||exit 0
git reset --hard origin/main >>/tmp/smarttv-update.log 2>&1||exit 0
sudo docker compose up -d --build >>/tmp/smarttv-update.log 2>&1||true
"$APP/.venv/bin/pip" install -q -r "$APP/host-agent/requirements.txt" >>/tmp/smarttv-update.log 2>&1||true
