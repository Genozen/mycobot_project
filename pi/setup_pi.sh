#!/usr/bin/env bash
set -euo pipefail

echo "=== myCobot 280 Pi Setup ==="
echo "This script installs mjpg-streamer and creates systemd services."
echo ""

# Upgrade pymycobot
echo "[1/4] Upgrading pymycobot..."
pip install pymycobot --upgrade

# Install mjpg-streamer dependencies
echo "[2/4] Installing mjpg-streamer dependencies..."
# Allow apt-get update to continue past stale third-party repo GPG keys
# (e.g. expired ROS keys, missing GitHub CLI keys on factory image)
sudo apt-get update || echo "  Warning: apt-get update had errors (likely stale GPG keys). Continuing..."
sudo apt-get install -y cmake libjpeg-dev gcc g++ git

# Build and install mjpg-streamer
if ! command -v mjpg_streamer &> /dev/null; then
    echo "[3/4] Building mjpg-streamer from source..."
    cd /tmp
    rm -rf /tmp/mjpg-streamer
    git clone https://github.com/jacksonliam/mjpg-streamer.git
    cd mjpg-streamer/mjpg-streamer-experimental
    mkdir -p _build && cd _build
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..
    make
    sudo make install
    cd ~
    rm -rf /tmp/mjpg-streamer
else
    echo "[3/4] mjpg-streamer already installed, skipping."
fi

# Install systemd services (server.py is shipped in this directory)
echo "[4/4] Installing systemd services..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo cp "$SCRIPT_DIR/mycobot_server.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/mjpg_streamer.service" /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable mycobot_server.service
sudo systemctl enable mjpg_streamer.service

echo ""
echo "=== Setup complete ==="
echo "Start services with: bash ~/Documents/robotics_club/mycobot_setup/start_services.sh"
echo "Or reboot and they will start automatically."
