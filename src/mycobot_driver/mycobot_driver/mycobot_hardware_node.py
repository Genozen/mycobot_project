"""
ROS 2 driver node for myCobot 280 Pi.

Connects to the robot via pymycobot TCP socket and bridges to ROS 2:
  - Publishes /joint_states at a configurable rate
  - Provides a FollowJointTrajectory action server for MoveIt2 integration
  - Provides gripper open/close service

Single TCP connection handles both arm and gripper (Server.py only accepts one client).
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
from std_srvs.srv import SetBool

from pymycobot import MyCobot280Socket


class MyCobotHardwareNode(Node):

    JOINT_NAMES = [
        'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6',
    ]

    def __init__(self):
        super().__init__('mycobot_hardware_node')

        self.declare_parameter('robot_ip', '192.168.1.169')
        self.declare_parameter('robot_port', 9000)
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('default_speed', 80)
        self.declare_parameter('gripper_speed', 80)

        ip = self.get_parameter('robot_ip').get_parameter_value().string_value
        port = self.get_parameter('robot_port').get_parameter_value().integer_value
        self._rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        self._speed = self.get_parameter('default_speed').get_parameter_value().integer_value
        self._gripper_speed = self.get_parameter('gripper_speed').get_parameter_value().integer_value

        self.get_logger().info(f'Connecting to myCobot at {ip}:{port}')
        self._mc = MyCobot280Socket(ip, port)
        time.sleep(0.5)

        try:
            if self._mc.get_fresh_mode() != 1:
                self._mc.set_fresh_mode(1)
                self.get_logger().info('Set fresh mode (responsive movement)')
        except Exception as e:
            self.get_logger().warn(f'Could not set fresh mode: {e}')

        self._lock = threading.Lock()

        # Joint state publisher
        self._js_pub = self.create_publisher(JointState, 'joint_states', 10)
        self._timer = self.create_timer(1.0 / self._rate, self._publish_joint_states)

        # Trajectory action server
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

        # Gripper service (shared TCP connection)
        self._gripper_srv = self.create_service(
            SetBool, 'gripper/set_state', self._gripper_callback
        )

        self.get_logger().info('myCobot hardware node ready (arm + gripper)')

    # ---- Joint State Publisher ----

    def _read_angles_rad(self):
        """Read current joint angles from the robot, returns radians or None."""
        try:
            with self._lock:
                angles_deg = self._mc.get_angles()
            if not isinstance(angles_deg, list) or len(angles_deg) != 6:
                return None
            return [math.radians(a) for a in angles_deg]
        except Exception:
            return None

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

            try:
                with self._lock:
                    self._mc.send_angles(angles_deg, self._speed)
            except Exception as e:
                self.get_logger().error(f'Failed to send angles: {e}')

            target_time = start_time + rclpy.duration.Duration(
                seconds=point.time_from_start.sec,
                nanoseconds=point.time_from_start.nanosec,
            )
            while self.get_clock().now() < target_time:
                time.sleep(0.02)

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

    # ---- Gripper Service ----

    def _gripper_callback(self, request, response):
        """SetBool: data=True -> close, data=False -> open."""
        state = 1 if request.data else 0
        action = 'close' if request.data else 'open'
        try:
            with self._lock:
                self._mc.set_gripper_state(state, self._gripper_speed)
            response.success = True
            response.message = f'Gripper {action}'
            self.get_logger().info(f'Gripper {action}')
        except Exception as e:
            response.success = False
            response.message = str(e)
            self.get_logger().error(f'Gripper error: {e}')
        return response


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
