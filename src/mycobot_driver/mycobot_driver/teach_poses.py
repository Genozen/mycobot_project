"""
Interactive pose recorder for myCobot 280 Pi.

Captures the robot's current joint angles and saves them as named poses
in the MoveIt2 SRDF file (<group_state> entries).

Usage (run while the MoveIt2 stack is active):
    ros2 run mycobot_driver teach_poses

Workflow:
  1. Launch the MoveIt2 stack (moveit_bringup.launch.py) in another terminal.
  2. In RViz2, drag the interactive marker to move the arm to a desired pose,
     then click "Plan & Execute" so the real robot moves there.
  3. In this terminal, press Enter to capture the current joint angles.
  4. Type a name for the pose (e.g. "pick", "place", "inspect").
  5. Repeat for as many poses as you want, then type "done" to finish.
  6. Recorded poses are written to the SRDF source file as <group_state> entries.

After recording, rebuild mycobot_moveit_config so MoveIt2 picks up the
new poses (they will appear in RViz2's MotionPlanning panel dropdown):
    colcon build --packages-select mycobot_moveit_config
    source install/setup.bash

The SRDF path defaults to the source tree so changes persist across rebuilds.
Override with:  --ros-args -p srdf_path:=/absolute/path/to/file.srdf
"""

import os
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


JOINT_NAMES = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']

DEFAULT_SRDF = os.path.normpath(os.path.join(
    os.path.realpath(os.path.dirname(__file__)),
    '..', '..', 'mycobot_moveit_config',
    'config', 'mycobot_280pi.srdf',
))


class TeachPoseNode(Node):
    def __init__(self):
        super().__init__('teach_poses')

        self.declare_parameter('srdf_path', DEFAULT_SRDF)
        self._srdf_path = (
            self.get_parameter('srdf_path')
            .get_parameter_value().string_value
        )

        self._latest_js = None
        self._sub = self.create_subscription(
            JointState, 'joint_states', self._js_cb, 10,
        )

    def _js_cb(self, msg: JointState):
        if len(msg.position) == 6:
            self._latest_js = list(msg.position)

    def get_current_pose(self) -> list | None:
        """Spin briefly and return the latest joint positions in radians."""
        self._latest_js = None
        deadline = self.get_clock().now() + rclpy.duration.Duration(seconds=2.0)
        while self._latest_js is None:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.get_clock().now() > deadline:
                return None
        return self._latest_js

    def run_interactive(self):
        recorded: list[tuple[str, list[float]]] = []

        print('\n=== myCobot Pose Recorder ===')
        print(f'SRDF target: {self._srdf_path}')
        print()
        print('How to use:')
        print('  1. In RViz2, drag the arm to a pose and "Plan & Execute".')
        print('  2. Once the robot reaches the pose, come back here and press Enter.')
        print('  3. Give the pose a name.')
        print('  4. Type "done" when finished.\n')

        # Wait for at least one joint_states message before starting
        print('Waiting for /joint_states ...', end=' ', flush=True)
        pose = self.get_current_pose()
        if pose is None:
            print('FAILED')
            print('ERROR: No /joint_states received. Is mycobot_hardware_node running?')
            return
        print('OK\n')

        while True:
            input('  Press [Enter] to capture the current pose...')

            pose = self.get_current_pose()
            if pose is None:
                print('  ERROR: Could not read joint states. Skipping.\n')
                continue

            angles_deg = [round(math.degrees(r), 2) for r in pose]
            angles_rad_4 = [round(r, 4) for r in pose]
            print(f'  Joint angles (deg): {angles_deg}')
            print(f'  Joint angles (rad): {angles_rad_4}')

            name = input('  Pose name (or "skip" to discard, "done" to finish): ').strip()
            if name.lower() == 'done':
                break
            if name.lower() == 'skip' or not name:
                print('  Skipped.\n')
                continue

            recorded.append((name, angles_rad_4))
            print(f'  Saved pose "{name}"\n')

        if not recorded:
            print('\nNo poses recorded. Exiting.')
            return

        print(f'\n--- Writing {len(recorded)} pose(s) to SRDF ---')
        self._write_to_srdf(recorded)
        print('\nDone! Rebuild to pick up the new poses in MoveIt2:')
        print('  colcon build --packages-select mycobot_moveit_config')
        print('  source install/setup.bash')

    def _write_to_srdf(self, poses: list[tuple[str, list[float]]]):
        path = self._srdf_path
        if not os.path.isfile(path):
            self.get_logger().error(f'SRDF not found: {path}')
            print(f'  ERROR: SRDF file not found at {path}')
            print('  Override with: --ros-args -p srdf_path:=/absolute/path')
            return

        tree = ET.parse(path)
        root = tree.getroot()

        existing_names = {
            gs.get('name') for gs in root.findall('group_state')
        }

        for name, rads in poses:
            if name in existing_names:
                print(f'  Updating existing pose "{name}"')
                for gs in root.findall('group_state'):
                    if gs.get('name') == name:
                        root.remove(gs)
                        break
            else:
                print(f'  Adding new pose "{name}"')

            gs = ET.SubElement(root, 'group_state', name=name, group='arm')
            for jname, val in zip(JOINT_NAMES, rads):
                ET.SubElement(gs, 'joint', name=jname, value=str(val))

        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)

        lines = reparsed.toprettyxml(indent='  ').split('\n')
        filtered = []
        for i, line in enumerate(lines):
            if i == 0 and line.startswith('<?xml'):
                filtered.append(line)
                continue
            if line.strip():
                filtered.append(line)
        output = '\n'.join(filtered) + '\n'

        with open(path, 'w') as f:
            f.write(output)

        self.get_logger().info(f'Wrote {len(poses)} pose(s) to {path}')


def main(args=None):
    rclpy.init(args=args)
    try:
        node = TeachPoseNode()
        node.run_interactive()
    except KeyboardInterrupt:
        print('\nInterrupted.')
    finally:
        rclpy.shutdown()
