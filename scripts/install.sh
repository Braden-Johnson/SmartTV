#!/usr/bin/env bash
set -euo pipefail
REPO="https://github.com/Braden-Johnson/SmartTV.git"
APP="$HOME/SmartTV"
echo "Installing SmartTV for $USER..."
sudo apt-get update
sudo apt-get install -y git docker.io python3 python3-venv python3-tk onboard xdotool curl
sudo apt-get install -y docker-compose-plugin || sudo apt-get install -y docker-compose
if [ -d "$APP/.git" ]; then git -C "$APP" pull --ff-only; else git clone "$REPO" "$APP"; fi
python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install --upgrade pip
"$APP/.venv/bin/pip" install -r "$APP/host-agent/requirements.txt"
mkdir -p "$APP/data" "$HOME/.config/systemd/user" "$HOME/.local/share/smarttv/chromium-profile"
cp "$APP/host-agent/smarttv-host.service" "$HOME/.config/systemd/user/smarttv-host.service"
sudo usermod -aG docker "$USER" || true
sudo systemctl enable --now docker
cd "$APP"
sudo docker compose up -d --build
systemctl --user daemon-reload
systemctl --user enable --now smarttv-host.service
loginctl enable-linger "$USER" || true
echo "SmartTV installed. Reboot with: sudo reboot"
