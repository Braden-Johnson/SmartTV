#!/usr/bin/env bash
set -euo pipefail
APP="$HOME/SmartTV"
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-tk xdotool curl
sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose
python3 -m venv "$APP/.venv";"$APP/.venv/bin/pip" install -r "$APP/host-agent/requirements.txt"
mkdir -p "$APP/data" "$HOME/.config/systemd/user" "$HOME/.local/share/smarttv/chromium-profile" "$HOME/Desktop"
cp "$APP/host-agent/smarttv-host.service" "$HOME/.config/systemd/user/"
cd "$APP";sudo docker compose up -d --build
cat > "$HOME/Desktop/SmartTV.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=SmartTV
Comment=Launch SmartTV Dashboard
Exec=systemctl --user restart smarttv-host.service
Icon=video-display
Terminal=false
Categories=AudioVideo;
EOF
chmod +x "$HOME/Desktop/SmartTV.desktop";gio set "$HOME/Desktop/SmartTV.desktop" metadata::trusted true 2>/dev/null || true
systemctl --user daemon-reload;systemctl --user enable --now smarttv-host.service
sudo loginctl enable-linger "$USER" || true
