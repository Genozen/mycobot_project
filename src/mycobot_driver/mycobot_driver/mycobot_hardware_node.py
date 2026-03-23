"""
ROS 2 driver node for myCobot 280 Pi.

Connects to the robot via pymycobot TCP socket and bridges to ROS 2:
  - Publishes /joint_states at a configurable rate
  - Provides a FollowJointTrajectory action server for MoveIt2 integration
"""

import math
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory

from pymycobot import MyCobot280Socket


class MyCobotHardwareNode(Node):

    JOINT_NAMES = [
        'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6',
    ]

    def __init__(self):
        super().__init__('mycobot_hardware_node')

        self.declare_parameter('robot_ip', '192.168.1.160')
        self.declare_parameter('robot_port', 9000)
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('default_speed', 80)

        ip = self.get_parameter('robot_ip').get_parameter_value().string_value
        port = self.get_parameter('robot_port').get_parameter_value().integer_value
        self._rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        self._speed = self.get_parameter('default_speed').get_parameter_value().integer_value

        self.get_logger().info(f'Connecting to myCobot at {ip}:{port}')
        self._mc = MyCobot280Socket(ip, port)
        time.sleep(0.5)

        if self._mc.get_fresh_mode() != 1:
            self._mc.set_fresh_mode(1)
            self.get_logger().info('Set fresh mode (responsive movement)')

        self._lock = threading.Lock()

        self._js_pub = self.create_publisher(JointState, 'joint_states', 10)
        self._timer = self.create_timer(1.0 / self._rate, self._publish_joint_states)

        cb_group = ReentrantCallbackGroup()
        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            'arm_controller/follow_joint_trajectory',
            execute_callback=self._execute_trajectory,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=cb_group,
        )

        self.get_logger().info('myCobot hardware node ready')

    # ---- Joint State Publisher ----

    def _read_angles_rad(self):
        """Read current joint angles from the robot, returns radians or None."""
        with self._lock:
            angles_deg = self._mc.get_angles()
        if not angles_deg or len(angles_deg) != 6:
            return None
        return [math.radians(a) for a in angles_deg]

    def _publish_joint_states(self):
        angles = self._read_angles_rad()
        if angles is None:
            return
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.JOINT_NAMES
        msg.position = angles
        self._js_pub.publish(msg)

    # ---- FollowJointTrajectory Action ----

    def _goal_callback(self, goal_request):
        self.get_logger().info('Received trajectory goal')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def _execute_trajectory(self, goal_handle):
        trajectory = goal_handle.request.trajectory
        feedback_msg = FollowJointTrajectory.Feedback()

        self.get_logger().info(
            f'Executing trajectory with {len(trajectory.points)} points'
        )

        start_time = self.get_clock().now()

        for i, point in enumerate(trajectory.points):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Trajectory canceled')
                return FollowJointTrajectory.Result()

            angles_deg = [math.degrees(p) for p in point.positions]

            with self._lock:
                self._mc.send_angles(angles_deg, self._speed)

            # Wait for the scheduled time of this trajectory point
            target_time = start_time + rclpy.duration.Duration(
                seconds=point.time_from_start.sec,
                nanoseconds=point.time_from_start.nanosec,
            )
            while self.get_clock().now() < target_time:
                time.sleep(0.02)

            # Publish feedback
            current_angles = self._read_angles_rad()
            if current_angles:
                feedback_msg.actual.positions = current_angles
                feedback_msg.desired.positions = list(point.positions)
                feedback_msg.error.positions = [
                    d - a for d, a in zip(point.positions, current_angles)
                ]
                goal_handle.publish_feedback(feedback_msg)

        goal_handle.succeed()
        self.get_logger().info('Trajectory execution complete')

        result = FollowJointTrajectory.Result()
        return result


def main(args=None):
    rclpy.init(args=args)
    node = MyCobotHardwareNode()
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
