#!/usr/bin/env bash
set -euo pipefail

PI_USER="${PI_USER:-er}"
PI_IP="${PI_IP:-192.168.1.169}"

echo "Syncing pi/ folder to ${PI_USER}@${PI_IP}:~/Documents/robotics_club/mycobot_setup/"
rsync -avz --progress "$(dirname "$0")/../pi/" "${PI_USER}@${PI_IP}:~/Documents/robotics_club/mycobot_setup/"
echo "Done. SSH in and run: bash ~/Documents/robotics_club/mycobot_setup/setup_pi.sh"
