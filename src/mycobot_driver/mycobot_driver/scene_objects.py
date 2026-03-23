"""
Publishes collision objects to the MoveIt2 planning scene.

Reads obstacle definitions from a YAML file (boxes for tables, walls, etc.)
and publishes them so the motion planner avoids collisions with the
physical environment.

Usage:
    ros2 run mycobot_driver scene_objects --ros-args -p obstacles_file:=/path/to/obstacles.yaml

The obstacles YAML format:
    frame_id: world
    obstacles:
      - name: table
        type: box
        dimensions: [1.0, 1.0, 0.02]   # [x, y, z] metres
        position: [0.0, 0.0, -0.45]
        orientation: [0.0, 0.0, 0.0]   # [roll, pitch, yaw] radians
"""

import os
import math
import yaml

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose


DEFAULT_OBSTACLES_FILE = os.path.normpath(os.path.join(
    os.path.realpath(os.path.dirname(__file__)),
    '..', '..', 'mycobot_moveit_config',
    'config', 'obstacles.yaml',
))


def euler_to_quaternion(roll, pitch, yaw):
    """Convert RPY angles (radians) to a quaternion (x, y, z, w)."""
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


class SceneObjectsNode(Node):
    def __init__(self):
        super().__init__('scene_objects')

        self.declare_parameter('obstacles_file', DEFAULT_OBSTACLES_FILE)
        self._obstacles_file = (
            self.get_parameter('obstacles_file')
            .get_parameter_value().string_value
        )

        self._scene_pub = self.create_publisher(
            PlanningScene, '/planning_scene', 10,
        )

        # Publish once after a short delay so move_group has time to start.
        # Then re-publish periodically in case move_group restarts.
        self._timer = self.create_timer(2.0, self._publish_obstacles)
        self._published = False

    def _load_obstacles(self):
        path = self._obstacles_file
        if not os.path.isfile(path):
            self.get_logger().error(f'Obstacles file not found: {path}')
            return None, []

        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        frame_id = data.get('frame_id', 'world')
        obstacles = data.get('obstacles', [])
        return frame_id, obstacles

    def _make_collision_object(self, frame_id, obs):
        co = CollisionObject()
        co.header.frame_id = frame_id
        co.header.stamp = self.get_clock().now().to_msg()
        co.id = obs['name']
        co.operation = CollisionObject.ADD

        if obs.get('type', 'box') == 'box':
            prim = SolidPrimitive()
            prim.type = SolidPrimitive.BOX
            dims = obs.get('dimensions', [0.1, 0.1, 0.1])
            prim.dimensions = [float(d) for d in dims]
            co.primitives.append(prim)

            pose = Pose()
            pos = obs.get('position', [0.0, 0.0, 0.0])
            pose.position.x = float(pos[0])
            pose.position.y = float(pos[1])
            pose.position.z = float(pos[2])

            rpy = obs.get('orientation', [0.0, 0.0, 0.0])
            qx, qy, qz, qw = euler_to_quaternion(
                float(rpy[0]), float(rpy[1]), float(rpy[2]),
            )
            pose.orientation.x = qx
            pose.orientation.y = qy
            pose.orientation.z = qz
            pose.orientation.w = qw
            co.primitive_poses.append(pose)

        return co

    def _publish_obstacles(self):
        frame_id, obstacles = self._load_obstacles()
        if not obstacles:
            if not self._published:
                self.get_logger().warn('No obstacles to publish')
            return

        scene = PlanningScene()
        scene.is_diff = True

        for obs in obstacles:
            co = self._make_collision_object(frame_id, obs)
            scene.world.collision_objects.append(co)

        self._scene_pub.publish(scene)

        if not self._published:
            names = [o['name'] for o in obstacles]
            self.get_logger().info(
                f'Published {len(obstacles)} collision object(s): {names}'
            )
            self._published = True


def main(args=None):
    rclpy.init(args=args)
    node = SceneObjectsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
