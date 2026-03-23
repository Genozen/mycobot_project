#!/usr/bin/env bash
set -euo pipefail

PI_USER="${PI_USER:-er}"
PI_IP="${PI_IP:-192.168.1.160}"

echo "Syncing pi/ folder to ${PI_USER}@${PI_IP}:~/mycobot_setup/"
rsync -avz --progress "$(dirname "$0")/../pi/" "${PI_USER}@${PI_IP}:~/mycobot_setup/"
echo "Done. SSH in and run: bash ~/mycobot_setup/setup_pi.sh"
