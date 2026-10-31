#!/usr/bin/env bash
set -euo pipefail
APP="$HOME/SmartTV"; cd "$APP"
git fetch origin main
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; then echo "Already current"; exit 0; fi
rm -rf "$HOME/.local/share/smarttv/rollback"; mkdir -p "$HOME/.local/share/smarttv/rollback"
git archive HEAD | tar -x -C "$HOME/.local/share/smarttv/rollback"
git pull --ff-only origin main
sudo docker compose up -d --build
"$APP/.venv/bin/pip" install -r "$APP/host-agent/requirements.txt"
systemctl --user restart smarttv-host.service
echo "Updated successfully"
