# mycobot_project (Legacy Reference Scripts)

Original pymycobot scripts that run directly on the myCobot 280 Pi via serial.
These are preserved as reference for the ROS 2 migration.

Full project demo: https://youtu.be/Jq-79XXTvu4

## Migration Map

These scripts are being migrated into ROS 2 packages in `src/`:

| Legacy Script | Migrated To | Status |
|---------------|-------------|--------|
| `mycobot_manager.py` | `mycobot_driver/mycobot_hardware_node.py` | Planned |
| `camera.py` | `mycobot_camera/camera_node.py` | Planned |
| `ducky_detector.py` | Future: ROS 2 perception node | Planned |
| `face_detector.py` | Future: ROS 2 perception node | Planned |
| `pick_and_place.py` | Future: MoveIt2 pick-and-place pipeline | Planned |
| `main.py` | Future: ROS 2 application node | Planned |
| `mycobot280_face_track_test.py` | Future: ROS 2 face tracking node | Planned |
| `blob_detect.py` | Reference only (HSV tuning utility) | -- |
| `hsv_tuning.py` | Reference only (HSV tuning utility) | -- |
| `draw_heart.py` | Reference only (demo script) | -- |
| `mediapipe_face_detect.py` | Merged into `face_detector.py` | -- |

## Key Constants (carry forward into ROS 2)

From `mycobot_manager.py`:
- `DUCK_DETECT_POSE = [115.5, -56.2, 284.6, -178.73, -4.05, -39.3]` (coords)
- `HUMAN_DETECT_POSE = [86.6, -121.2, 389.9, -80.09, 42.7, -105.22]` (coords)
- Refresh mode: `set_fresh_mode(1)` for responsive movement
- Gripper speed: 80

From `main.py`:
- `PIXEL_TO_MM_RATIO = 0.497` (camera calibration)
- `DUCK_CENTER = (230, 230)` (pixel coordinates)

## API Documentation

- https://docs.elephantrobotics.com/docs/mycobot_280_pi_en/3-FunctionsAndApplications/6.developmentGuide/python/2_API.html
- https://github.dev/elephantrobotics/pymycobot (look for `generate.py`, `mycobot.py`)

## Pi Tips (from original development)

### Xpra display forwarding (superseded by mjpg-streamer in the ROS 2 workspace)

```bash
# On raspi
sudo apt-get update && sudo apt-get install xpra
xpra start :99 --start=xterm
export DISPLAY=:99

# On host
xpra attach ssh://er@192.168.1.169/99
```

### Speed up Raspi with swap

```bash
free -h
sudo dd if=/dev/zero of=/swapfile bs=1024 count=4194304  # 4GB
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
free -h

# To turn off
sudo swapoff /swapfile
```

### X11 forwarding

```bash
ssh -Y er@192.168.1.169
# If not working, on the Pi:
# sudo nano /etc/ssh/sshd_config -> set X11Forwarding yes
# sudo systemctl restart ssh
```
