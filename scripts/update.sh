#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/SmartTV";git fetch origin main;git reset --hard origin/main;sudo docker compose up -d --build;"$HOME/SmartTV/.venv/bin/pip" install -r host-agent/requirements.txt;cp host-agent/smarttv-host.service "$HOME/.config/systemd/user/";systemctl --user daemon-reload;systemctl --user restart smarttv-host.service
