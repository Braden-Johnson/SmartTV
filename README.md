# SmartTV v1.0
A Raspberry Pi 5 Smart TV launcher with a Portainer-managed Flask backend and a host-level Chromium controller.

## First installation
1. Upload this repository to `Braden-Johnson/SmartTV` on GitHub.
2. On the Pi run:
   `git clone https://github.com/Braden-Johnson/SmartTV.git ~/SmartTV`
3. Run:
   `chmod +x ~/SmartTV/scripts/*.sh && ~/SmartTV/scripts/install.sh`
4. Reboot:
   `sudo reboot`

Dashboard: http://127.0.0.1:8765
Host agent: http://127.0.0.1:8766/status

## Portainer
The `smarttv-backend` container appears automatically after install. The compose stack uses host networking so it can reach Glances at port 61208 and the host agent at port 8766.

## Troubleshooting
- Backend logs: `cd ~/SmartTV && sudo docker compose logs -f`
- Host agent logs: `journalctl --user -u smarttv-host.service -f`
- Restart: `systemctl --user restart smarttv-host.service`
- Update: `~/SmartTV/scripts/update.sh`
