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
sudo apt-get update
sudo apt-get install -y cmake libjpeg-dev gcc g++ git

# Build and install mjpg-streamer
if ! command -v mjpg_streamer &> /dev/null; then
    echo "[3/4] Building mjpg-streamer from source..."
    cd /tmp
    git clone https://github.com/350d/mjpg-streamer.git
    cd mjpg-streamer/mjpg-streamer-experimental
    mkdir -p _build && cd _build
    cmake ..
    make
    sudo make install
    cd ~
    rm -rf /tmp/mjpg-streamer
else
    echo "[3/4] mjpg-streamer already installed, skipping."
fi

# Clone pymycobot if not present (for Server.py)
PYMYCOBOT_DIR="$HOME/pymycobot"
if [ ! -d "$PYMYCOBOT_DIR" ]; then
    echo "[3.5/4] Cloning pymycobot repo for Server.py..."
    git clone https://github.com/elephantrobotics/pymycobot.git "$PYMYCOBOT_DIR"
fi

# Install systemd services
echo "[4/4] Installing systemd services..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo cp "$SCRIPT_DIR/mycobot_server.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/mjpg_streamer.service" /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable mycobot_server.service
sudo systemctl enable mjpg_streamer.service

echo ""
echo "=== Setup complete ==="
echo "Start services with: bash ~/mycobot_setup/start_services.sh"
echo "Or reboot and they will start automatically."
