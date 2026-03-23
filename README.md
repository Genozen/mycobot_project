# myCobot 280 Pi -- ROS 2 Workspace

Remote-control a myCobot 280 Pi over the network from a Desktop PC using ROS 2 Humble and MoveIt2.

## Architecture

The Pi runs two lightweight servers (no ROS 2 needed). All ROS 2 nodes run on the Desktop.

```
Desktop PC (Ubuntu 22.04 / ROS 2 Humble)         myCobot 280 Pi (Ubuntu 20.04)
┌──────────────────────────────────────┐         ┌─────────────────────────────┐
│  MoveIt2 Planning                    │         │  pymycobot Server.py :9000  │
│  mycobot_driver ──── TCP :9000 ──────┼────────►│    └── /dev/ttyAMA0 ──► Arm │
│    ├── /joint_states                 │         │                             │
│    ├── /follow_joint_trajectory      │         │  mjpg-streamer :8080        │
│    └── /gripper services             │         │    └── /dev/video0 ──► Cam  │
│  mycobot_camera ─── HTTP :8080 ──────┼────────►│                             │
│    └── /camera/image_raw             │         └─────────────────────────────┘
│  robot_state_publisher               │
│  RViz2                               │
└──────────────────────────────────────┘
```

## Repository Layout

```
mycobot_project/               # <-- this is the ROS 2 workspace root
├── src/
│   ├── mycobot_description/    # URDF, meshes, RViz config
│   ├── mycobot_driver/         # Arm + gripper control via pymycobot TCP
│   ├── mycobot_camera/         # Camera stream consumer (MJPEG -> ROS 2)
│   ├── mycobot_moveit_config/  # MoveIt2 planning config
│   └── mycobot_bringup/        # Top-level launch files
├── legacy/                     # Original pymycobot scripts (reference)
├── pi/                         # Scripts for the Pi (no ROS 2)
└── scripts/                    # Developer utility scripts
```

## Prerequisites

### Desktop PC
- Ubuntu 22.04
- ROS 2 Humble (`sudo apt install ros-humble-desktop`)
- MoveIt 2 (`sudo apt install ros-humble-moveit`)
- pymycobot (`pip install pymycobot`)
- cv_bridge (`sudo apt install ros-humble-cv-bridge`)

### myCobot 280 Pi
- Factory image (Ubuntu 20.04) -- no changes required
- Connected to the same network as the Desktop
- Default IP: `192.168.1.160`, user: <>, password: <>

## Quick Start

### 1. One-time Pi setup

```bash
# From the Desktop, copy setup scripts to the Pi and run them
scp -r pi/ er@192.168.1.160:~/mycobot_setup/
ssh er@192.168.1.160 'bash ~/mycobot_setup/setup_pi.sh'
```

### 2. Start Pi services

```bash
ssh er@192.168.1.160 'bash ~/mycobot_setup/start_services.sh'
# Verify camera: open http://192.168.1.160:8080/?action=stream in a browser
```

### 3. Build and run (Desktop)

```bash
source /opt/ros/humble/setup.bash
cd mycobot_project
colcon build --symlink-install
source install/setup.bash

# Visualize the URDF
ros2 launch mycobot_description display.launch.py

# Connect to robot (driver + gripper + camera)
ros2 launch mycobot_bringup robot_bringup.launch.py robot_ip:=192.168.1.160

# Full MoveIt2 stack
ros2 launch mycobot_bringup moveit_bringup.launch.py
```

## ROS 2 Topics and Services

| Name | Type | Description |
|------|------|-------------|
| `/joint_states` | `sensor_msgs/JointState` | Current joint angles (20 Hz) |
| `/camera/image_raw` | `sensor_msgs/Image` | Camera feed from Pi |
| `/gripper/set_state` | Service | Open (0) / close (1) gripper |
| `/gripper/set_value` | Service | Set gripper position 0-100 |
| `arm_controller/follow_joint_trajectory` | Action | MoveIt2 trajectory execution |

## Future: Isaac Sim Integration

The URDF and ROS 2 topic structure are designed for direct integration with
NVIDIA Isaac Sim via the ROS 2 bridge for RL/IL workflows.
