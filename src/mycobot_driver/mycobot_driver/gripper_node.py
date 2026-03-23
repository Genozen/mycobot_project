"""
ROS 2 node for myCobot 280 Pi gripper control.

Provides services for opening/closing the gripper and setting proportional values.
Connects to the same pymycobot TCP server as the hardware node.
"""

import time
import threading

import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool
from sensor_msgs.msg import JointState

from pymycobot import MyCobot280Socket


class GripperNode(Node):

    def __init__(self):
        super().__init__('gripper_node')

        self.declare_parameter('robot_ip', '192.168.1.169')
        self.declare_parameter('robot_port', 9000)
        self.declare_parameter('gripper_speed', 80)
        self.declare_parameter('publish_rate', 5.0)

        ip = self.get_parameter('robot_ip').get_parameter_value().string_value
        port = self.get_parameter('robot_port').get_parameter_value().integer_value
        self._speed = self.get_parameter('gripper_speed').get_parameter_value().integer_value
        rate = self.get_parameter('publish_rate').get_parameter_value().double_value

        self.get_logger().info(f'Gripper node connecting to {ip}:{port}')
        self._mc = MyCobot280Socket(ip, port)
        time.sleep(0.5)

        self._lock = threading.Lock()

        self._set_state_srv = self.create_service(
            SetBool, 'gripper/set_state', self._set_state_callback
        )

        self._gripper_pub = self.create_publisher(JointState, 'gripper/state', 10)
        self._timer = self.create_timer(1.0 / rate, self._publish_gripper_state)

        self.get_logger().info('Gripper node ready (gripper/set_state service)')

    def _set_state_callback(self, request, response):
        """SetBool: data=True -> close, data=False -> open."""
        state = 1 if request.data else 0
        action = 'close' if request.data else 'open'
        try:
            with self._lock:
                self._mc.set_gripper_state(state, self._speed)
            response.success = True
            response.message = f'Gripper {action}'
            self.get_logger().info(f'Gripper {action}')
        except Exception as e:
            response.success = False
            response.message = str(e)
            self.get_logger().error(f'Gripper error: {e}')
        return response

    def _publish_gripper_state(self):
        try:
            with self._lock:
                value = self._mc.get_gripper_value()
            if value is not None:
                msg = JointState()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.name = ['gripper']
                msg.position = [float(value) / 100.0]
                self._gripper_pub.publish(msg)
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = GripperNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
