"""
ROS 2 driver node for myCobot 280 Pi.

Connects to the robot via pymycobot TCP socket and bridges to ROS 2:
  - Publishes /joint_states at a configurable rate (6 arm joints + 1 gripper joint)
  - Provides a FollowJointTrajectory action server for MoveIt2 arm planning
  - Provides a GripperCommand action server for MoveIt2 gripper planning
    (action: /gripper_controller/gripper_cmd)
  - Provides gripper open/close via /gripper/set_state (SetBool) for scripts

Single TCP connection handles both arm and gripper (Server.py only accepts one client).
"""

import math
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory, GripperCommand
from std_srvs.srv import SetBool

from pymycobot import MyCobot280Socket


class MyCobotHardwareNode(Node):

    JOINT_NAMES = [
        'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6',
    ]
    GRIPPER_JOINT_NAME = 'gripper_finger_joint'
    # URDF joint position (radians) for each semantic endpoint. These match
    # what the gripper_left3 mesh actually shows in RViz: at joint=0 the
    # mesh visually looks open, and at joint=0.5 it looks closed.
    # The URDF <limit lower/upper> still bounds the joint to [0.0, 0.5];
    # these constants assign meaning to those endpoints.
    GRIPPER_JOINT_OPEN_POS = 0.0
    GRIPPER_JOINT_CLOSED_POS = 0.5

    def __init__(self):
        super().__init__('mycobot_hardware_node')

        self.declare_parameter('robot_ip', '192.168.1.169')
        self.declare_parameter('robot_port', 9000)
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('default_speed', 80)
        self.declare_parameter('gripper_speed', 80)
        # Maps MoveIt joint position to pymycobot's set_gripper_value(0..100).
        # NOTE: The official Elephant Robotics docs say 0=open / 100=close, but
        # our myCobot 280 Pi firmware is empirically inverted (100=open,
        # 0=close). Defaults below match what this hardware actually does.
        # If you swap to a docs-compliant gripper, override at launch with:
        #   -p gripper_open_value:=0 -p gripper_closed_value:=100
        self.declare_parameter('gripper_open_value', 100)
        self.declare_parameter('gripper_closed_value', 0)

        ip = self.get_parameter('robot_ip').get_parameter_value().string_value
        port = self.get_parameter('robot_port').get_parameter_value().integer_value
        self._rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        self._speed = self.get_parameter('default_speed').get_parameter_value().integer_value
        self._gripper_speed = self.get_parameter('gripper_speed').get_parameter_value().integer_value
        self._g_open = self.get_parameter('gripper_open_value').get_parameter_value().integer_value
        self._g_closed = self.get_parameter('gripper_closed_value').get_parameter_value().integer_value

        # Last known gripper joint position (radians). Used as fallback when
        # get_gripper_value() fails or hasn't been polled yet so we never
        # publish a stale/missing value into /joint_states.
        self._gripper_pos = self.GRIPPER_JOINT_OPEN_POS  # assume open at startup

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

        # Each callback group gets its own thread in MultiThreadedExecutor,
        # preventing the 20Hz timer from starving the service/action callbacks.
        action_cb_group = ReentrantCallbackGroup()
        service_cb_group = MutuallyExclusiveCallbackGroup()

        self._action_server = ActionServer(
            self,
            FollowJointTrajectory,
            'arm_controller/follow_joint_trajectory',
            execute_callback=self._execute_trajectory,
            goal_callback=self._goal_callback,
            cancel_callback=self._cancel_callback,
            callback_group=action_cb_group,
        )

        # GripperCommand action for MoveIt2. Action name is composed by
        # moveit_simple_controller_manager as <controller_name>/<action_ns>,
        # which matches "gripper_controller" + "gripper_cmd" in
        # moveit_controllers.yaml.
        self._gripper_action_server = ActionServer(
            self,
            GripperCommand,
            'gripper_controller/gripper_cmd',
            execute_callback=self._execute_gripper_command,
            callback_group=action_cb_group,
        )

        # SetBool service kept for scripts/CLI/teleop convenience.
        self._gripper_srv = self.create_service(
            SetBool, 'gripper/set_state', self._gripper_callback,
            callback_group=service_cb_group,
        )

        self.get_logger().info(
            'myCobot hardware node ready '
            '(arm trajectory + gripper action + gripper service)'
        )

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

    # ---- URDF joint pos <-> pymycobot value mapping ----
    #
    # We use a normalized "openness" scalar t in [0.0, 1.0] (0 = fully closed,
    # 1 = fully open) as the intermediate representation, so neither side has
    # to know which end of the other's range is open vs closed.
    # These helpers are the single source of truth for both directions.

    def _openness_to_joint_pos(self, t: float) -> float:
        return (
            self.GRIPPER_JOINT_CLOSED_POS
            + t * (self.GRIPPER_JOINT_OPEN_POS - self.GRIPPER_JOINT_CLOSED_POS)
        )

    def _joint_pos_to_openness(self, pos_rad: float) -> float:
        denom = self.GRIPPER_JOINT_OPEN_POS - self.GRIPPER_JOINT_CLOSED_POS
        if denom == 0:
            return 0.0
        t = (pos_rad - self.GRIPPER_JOINT_CLOSED_POS) / denom
        return max(0.0, min(1.0, t))

    def _joint_pos_to_gripper_value(self, pos_rad: float) -> int:
        """URDF joint position (rad) -> pymycobot value (int 0..100)."""
        t = self._joint_pos_to_openness(pos_rad)
        value = self._g_closed + t * (self._g_open - self._g_closed)
        return int(round(value))

    def _gripper_value_to_joint_pos(self, value) -> float | None:
        """pymycobot value (0..100) -> URDF joint position (rad)."""
        if value is None or not isinstance(value, (int, float)):
            return None
        denom = self._g_open - self._g_closed
        if denom == 0:
            return None
        t = max(0.0, min(1.0, (float(value) - self._g_closed) / denom))
        return self._openness_to_joint_pos(t)

    def _read_gripper_pos_rad(self):
        """Read gripper from robot and map to URDF joint range. None on failure."""
        try:
            with self._lock:
                value = self._mc.get_gripper_value()
            return self._gripper_value_to_joint_pos(value)
        except Exception:
            return None

    def _publish_joint_states(self):
        angles = self._read_angles_rad()
        if angles is None:
            return

        # Refresh cached gripper position; fall back to last known value
        # so MoveIt's state monitor never sees a missing joint.
        gripper = self._read_gripper_pos_rad()
        if gripper is not None:
            self._gripper_pos = gripper

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.JOINT_NAMES + [self.GRIPPER_JOINT_NAME]
        msg.position = angles + [self._gripper_pos]
        self._js_pub.publish(msg)

    # ---- FollowJointTrajectory Action ----

    def _goal_callback(self, goal_request):
        self.get_logger().info('Received trajectory goal')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def _wait_until_reached(self, target_deg, tolerance_deg=5.0, timeout=8.0):
        """Poll joint angles until robot reaches target or timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with self._lock:
                    current = self._mc.get_angles()
                if isinstance(current, list) and len(current) == 6:
                    max_err = max(abs(c - t) for c, t in zip(current, target_deg))
                    if max_err < tolerance_deg:
                        return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def _execute_trajectory(self, goal_handle):
        trajectory = goal_handle.request.trajectory
        feedback_msg = FollowJointTrajectory.Feedback()
        points = trajectory.points
        n = len(points)

        if n == 0:
            goal_handle.succeed()
            return FollowJointTrajectory.Result()

        # The first point is the current position — skip it to avoid
        # the gravity-drop caused by re-commanding the current pose.
        # For short trajectories just send the final target directly.
        if n <= 6:
            waypoint_indices = [n - 1]
        else:
            # Pick ~3 intermediate guide points + the final target.
            # Fewer stops = smoother motion via mid-flight redirection.
            quarter = n // 4
            waypoint_indices = [quarter, n // 2, 3 * quarter, n - 1]

        self.get_logger().info(
            f'Executing trajectory: {n} points, '
            f'sending {len(waypoint_indices)} waypoints'
        )

        for seq, idx in enumerate(waypoint_indices):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Trajectory canceled')
                return FollowJointTrajectory.Result()

            point = points[idx]
            angles_deg = [math.degrees(p) for p in point.positions]
            is_last = (idx == waypoint_indices[-1])

            try:
                with self._lock:
                    self._mc.send_angles(angles_deg, self._speed)
            except Exception as e:
                self.get_logger().error(f'Failed to send angles: {e}')
                continue

            if is_last:
                self._wait_until_reached(angles_deg, tolerance_deg=3.0, timeout=10.0)
            else:
                # Minimal delay — just enough for the TCP command to register.
                # The next send_angles() redirects the arm mid-flight,
                # creating smooth blended motion instead of stop-and-go.
                time.sleep(0.15)

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
        if request.data:
            value = self._g_closed
            joint_pos = self.GRIPPER_JOINT_CLOSED_POS
            action = 'close'
        else:
            value = self._g_open
            joint_pos = self.GRIPPER_JOINT_OPEN_POS
            action = 'open'
        try:
            with self._lock:
                self._mc.set_gripper_value(value, self._gripper_speed)
            self._gripper_pos = joint_pos
            response.success = True
            response.message = f'Gripper {action} (value={value})'
            self.get_logger().info(f'Gripper {action} -> set_gripper_value({value})')
        except Exception as e:
            response.success = False
            response.message = str(e)
            self.get_logger().error(f'Gripper error: {e}')
        return response

    # ---- GripperCommand Action (MoveIt2) ----

    def _execute_gripper_command(self, goal_handle):
        """control_msgs/GripperCommand -> set_gripper_value with continuous mapping.

        MoveIt sends a target joint position in URDF range
        [GRIPPER_JOINT_MIN, GRIPPER_JOINT_MAX]. We linearly map that to the
        pymycobot value range using the (parameterized) open/closed endpoints,
        so partial-open commands actually drive to a partial-open position.
        """
        target = goal_handle.request.command.position
        # Clamp to the URDF range — MoveIt should already do this, but be safe.
        # Use min/max in case OPEN/CLOSED swap which end is numerically larger.
        lo = min(self.GRIPPER_JOINT_OPEN_POS, self.GRIPPER_JOINT_CLOSED_POS)
        hi = max(self.GRIPPER_JOINT_OPEN_POS, self.GRIPPER_JOINT_CLOSED_POS)
        clamped = max(lo, min(hi, target))
        value = self._joint_pos_to_gripper_value(clamped)

        result = GripperCommand.Result()
        try:
            with self._lock:
                self._mc.set_gripper_value(value, self._gripper_speed)
            self._gripper_pos = clamped

            # Give the gripper a moment to actuate before reporting success.
            # The pymycobot call is fire-and-forget; this is a pragmatic delay.
            time.sleep(0.5)

            goal_handle.succeed()
            result.position = clamped
            result.effort = 0.0
            result.stalled = False
            result.reached_goal = True
            self.get_logger().info(
                f'GripperCommand: target={target:.3f} rad -> '
                f'set_gripper_value({value})'
            )
        except Exception as e:
            self.get_logger().error(f'GripperCommand error: {e}')
            goal_handle.abort()
            result.position = self._gripper_pos
            result.reached_goal = False
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
        try:
            rclpy.shutdown()
        except Exception:
            pass
