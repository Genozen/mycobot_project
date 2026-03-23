"""
ROS 2 camera node for myCobot 280 Pi.

Consumes an MJPEG HTTP stream from mjpg-streamer running on the Pi
and publishes sensor_msgs/Image on /camera/image_raw.
"""

import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge


class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameter('camera_url', 'http://192.168.1.169:8080/?action=stream')
        self.declare_parameter('frame_rate', 30.0)
        self.declare_parameter('frame_id', 'camera_link')

        url = self.get_parameter('camera_url').get_parameter_value().string_value
        rate = self.get_parameter('frame_rate').get_parameter_value().double_value
        self._frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self._bridge = CvBridge()
        self._image_pub = self.create_publisher(Image, 'camera/image_raw', 10)
        self._info_pub = self.create_publisher(CameraInfo, 'camera/camera_info', 10)

        self.get_logger().info(f'Opening camera stream: {url}')
        self._cap = cv2.VideoCapture(url)

        if not self._cap.isOpened():
            self.get_logger().error(f'Failed to open camera stream at {url}')
            self.get_logger().error(
                'Make sure mjpg-streamer is running on the Pi: '
                'ssh er@192.168.1.169 "bash ~/Documents/robotics_club/mycobot_setup/start_services.sh"'
            )
        else:
            self.get_logger().info('Camera stream connected')

        self._timer = self.create_timer(1.0 / rate, self._capture_and_publish)
        self._width = None
        self._height = None

    def _capture_and_publish(self):
        if not self._cap.isOpened():
            return

        ret, frame = self._cap.read()
        if not ret:
            return

        if self._width is None:
            self._height, self._width = frame.shape[:2]
            self.get_logger().info(f'Streaming {self._width}x{self._height}')

        stamp = self.get_clock().now().to_msg()

        img_msg = self._bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        img_msg.header.stamp = stamp
        img_msg.header.frame_id = self._frame_id
        self._image_pub.publish(img_msg)

        info_msg = CameraInfo()
        info_msg.header.stamp = stamp
        info_msg.header.frame_id = self._frame_id
        info_msg.width = self._width
        info_msg.height = self._height
        self._info_pub.publish(info_msg)

    def destroy_node(self):
        if self._cap is not None:
            self._cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
