# myCobot 280 Pi -- ROS 2 Workspace

Remote-control a myCobot 280 Pi over the network from a Desktop PC using ROS 2 Humble and MoveIt2.

## Architecture

The Pi runs two lightweight servers (no ROS 2 needed). All ROS 2 nodes run on the Desktop.

A **single** `mycobot_hardware_node` maintains one TCP connection to the Pi's
`pymycobot Server.py` and handles both arm control and gripper control.
This is required because `Server.py` only accepts one client at a time.

```
Desktop PC (Ubuntu 22.04 / ROS 2 Humble)         myCobot 280 Pi (Ubuntu 20.04)
┌──────────────────────────────────────┐         ┌──────────────────────────────┐
│  MoveIt2 Planning                    │         │  pymycobot Server.py :9000   │
│  mycobot_hardware_node ── TCP :9000 ─┼────────►│    └── /dev/ttyAMA0 ──► Arm  │
│    ├── /joint_states                 │         │                              │
│    ├── /follow_joint_trajectory      │         │  camera_stream.py :8080      │
│    └── /gripper/set_state            │         │    └── /dev/video0 ──► Cam   │
│  camera_node ──── HTTP :8080 ────────┼────────►│                              │
│    └── /camera/image_raw             │         └──────────────────────────────┘
│  robot_state_publisher               │
│  RViz2                               │
└──────────────────────────────────────┘
```

## Repository Layout

```
mycobot_project/               # <-- this is the ROS 2 workspace root
├── src/
│   ├── mycobot_description/   # URDF (arm + camera + gripper), meshes, RViz config
│   ├── mycobot_driver/        # Arm + gripper control + pose recorder
│   ├── mycobot_camera/        # Camera stream consumer (MJPEG -> ROS 2 Image)
│   ├── mycobot_moveit_config/ # MoveIt2 planning config (SRDF, kinematics, OMPL)
│   └── mycobot_bringup/       # Top-level launch files
├── legacy/                    # Original pymycobot scripts (reference)
├── pi/                        # Scripts & services for the Pi (no ROS 2)
│   ├── setup_pi.sh            # One-time Pi dependency installer
│   ├── start_services.sh      # Start arm server + camera stream
│   ├── server.py              # TCP-to-serial bridge (raw binary, pymycobot 4.x compatible)
│   ├── camera_stream.py       # Python MJPEG HTTP server (replaces mjpg-streamer)
│   ├── mycobot_server.service # systemd unit for server.py
│   └── mjpg_streamer.service  # systemd unit for camera_stream.py
└── scripts/                   # Developer utility scripts (sync_to_pi.sh)
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
- Default IP: `192.168.1.169`, user: `er`, password: `elephant`

## Quick Start

### 1. One-time Pi setup

```bash
# From the Desktop, copy setup scripts to the Pi and run them
scp -r pi/ er@192.168.1.169:~/Documents/robotics_club/mycobot_setup/
ssh er@192.168.1.169 'bash ~/Documents/robotics_club/mycobot_setup/setup_pi.sh'
```

### 2. Start Pi services

```bash
ssh er@192.168.1.169 'bash ~/Documents/robotics_club/mycobot_setup/start_services.sh'
# Verify camera: open http://192.168.1.169:8080/?action=stream in a browser

# to stop the service
ssh er@192.168.1.169 'sudo systemctl stop mycobot_server.service'
```

### 3. Build and run (Desktop)

```bash
pip install pymycobot

source /opt/ros/humble/setup.bash
cd mycobot_project
colcon build --symlink-install
source install/setup.bash

# Visualize the URDF only
ros2 launch mycobot_description display.launch.py

# Driver only (arm + gripper, no camera)
ros2 launch mycobot_driver driver.launch.py

# Connect to robot (driver + camera + robot_state_publisher)
ros2 launch mycobot_bringup robot_bringup.launch.py

# Full MoveIt2 stack (driver + move_group + RViz2)
ros2 launch mycobot_bringup moveit_bringup.launch.py
```

## Collision Obstacles

The planner avoids physical obstacles (table, walls) defined in
`src/mycobot_moveit_config/config/obstacles.yaml`.
They are automatically loaded when the MoveIt2 stack launches and
appear as green shapes in RViz2.

Edit the YAML to match your physical setup — dimensions are in metres,
positions are in the `world` frame (robot mount point at origin, Z up):

```yaml
obstacles:
  - name: table
    type: box
    dimensions: [1.0, 1.0, 0.02]   # [x, y, z] size
    position: [0.0, 0.0, -0.45]    # 45cm below mount
    orientation: [0.0, 0.0, 0.0]   # [roll, pitch, yaw]
```

After editing, rebuild and re-source:
```bash
colcon build --packages-select mycobot_moveit_config
source install/setup.bash
```

## Recording Named Poses (Teach Mode)

Record the robot's current position as a named pose for MoveIt2.
Use RViz2 to move the arm to a desired position, then capture it:

```bash
# Terminal 1: Launch the full MoveIt2 stack
ros2 launch mycobot_bringup moveit_bringup.launch.py

# Terminal 2: Start the pose recorder
ros2 run mycobot_driver teach_poses
```

In the recorder terminal:
1. In RViz2, drag the interactive marker and click **Plan & Execute** to move the arm.
2. Once the arm reaches the desired pose, press **Enter** in the recorder terminal.
3. Type a name for the pose (e.g. `pick`, `place`, `inspect`).
4. Repeat for more poses, or type `done` to finish.
5. Rebuild the config package so MoveIt2 loads the new poses:

```bash
colcon build --packages-select mycobot_moveit_config
source install/setup.bash
```

Recorded poses are saved as `<group_state>` entries in the SRDF source file
and appear in the **Goal State** dropdown in RViz2's MotionPlanning panel.

## ROS 2 Topics and Services

| Name | Type | Description |
|------|------|-------------|
| `/joint_states` | `sensor_msgs/JointState` | Current joint angles (20 Hz) |
| `/camera/image_raw` | `sensor_msgs/Image` | Camera feed from Pi |
| `/camera/camera_info` | `sensor_msgs/CameraInfo` | Camera metadata |
| `/gripper/set_state` | `std_srvs/SetBool` | Open (`false`) / close (`true`) gripper |
| `arm_controller/follow_joint_trajectory` | Action (`FollowJointTrajectory`) | MoveIt2 trajectory execution |

## Node Parameters

### mycobot_hardware_node

| Parameter | Default | Description |
|-----------|---------|-------------|
| `robot_ip` | `192.168.1.169` | Pi IP address |
| `robot_port` | `9000` | pymycobot TCP port |
| `publish_rate` | `20.0` | Joint state publish rate (Hz) |
| `default_speed` | `80` | Arm movement speed (0-100) |
| `gripper_speed` | `80` | Gripper open/close speed (0-100) |

### camera_node

| Parameter | Default | Description |
|-----------|---------|-------------|
| `camera_url` | `http://192.168.1.169:8080/?action=stream` | MJPEG stream URL |
| `frame_rate` | `30.0` | Capture rate (Hz) |
| `frame_id` | `camera_link` | TF frame for camera images |

## Future: Isaac Sim Integration

The URDF and ROS 2 topic structure are designed for direct integration with
NVIDIA Isaac Sim via the ROS 2 bridge for RL/IL workflows.
