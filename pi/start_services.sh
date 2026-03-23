#!/usr/bin/env bash
set -euo pipefail

echo "Starting myCobot services..."

sudo systemctl start mycobot_server.service
echo "  pymycobot TCP server (port 9000): $(sudo systemctl is-active mycobot_server.service)"

sudo systemctl start mjpg_streamer.service
echo "  mjpg-streamer camera (port 8080): $(sudo systemctl is-active mjpg_streamer.service)"

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "Arm TCP:    $IP:9000"
echo "Camera:     http://$IP:8080/?action=stream"
