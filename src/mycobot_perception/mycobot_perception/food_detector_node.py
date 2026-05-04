"""
ROS 2 food-detection node for myCobot 280 Pi.

Subscribes to a sensor_msgs/Image stream (default: /camera/image_raw),
runs Ultralytics inference, and publishes:

  1. A CV2 window with bboxes + labels (for humans).
  2. The annotated frame on /perception/food_detections/image
     (so RViz2 / other consumers can subscribe).
  3. Structured detections on /perception/food_detections as
     vision_msgs/Detection2DArray (for downstream pick-and-place nodes).

Two modes (toggled by the `vocabulary` parameter):

  - COCO mode (vocabulary empty, default): YOLOv11 trained on COCO,
    filtered to the 10 COCO food classes via `food_class_ids`.
    Fastest, smallest model (~6 MB).

  - Open-vocabulary mode (vocabulary non-empty): YOLO-World v2,
    detects ANY noun you list (e.g. ["strawberry", "ketchup bottle"]).
    No retraining needed, ~50 MB model, slightly slower.
    `food_class_ids` is ignored in this mode -- the vocabulary IS
    the class list.

Design notes
------------
- QoS is BEST_EFFORT, depth=1 -- camera frames are "latest wins".
- `cv2.waitKey(1)` is mandatory after `imshow` to pump the GUI loop.
- All tunables are ROS 2 parameters; same binary works headless
  (`show_window:=false`) or with a custom-trained .pt
  (`model_path:=/path/to/my_food.pt`).
"""

from __future__ import annotations

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.exceptions import ParameterUninitializedException

from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)

from ultralytics import YOLO


# COCO class IDs that are food. The Ultralytics YOLOv11 default model is
# trained on COCO, so these IDs are stable.
COCO_FOOD_CLASS_IDS = [46, 47, 48, 49, 50, 51, 52, 53, 54, 55]
# 46 banana, 47 apple, 48 sandwich, 49 orange, 50 broccoli,
# 51 carrot, 52 hot dog, 53 pizza, 54 donut, 55 cake

# Default model used when `vocabulary` is non-empty. YOLO-World v2 supports
# `set_classes(...)` for open-vocabulary detection (any noun via CLIP text
# embeddings). User can override via `model_path`.
DEFAULT_OPEN_VOCAB_MODEL = 'yolov8s-worldv2.pt'


class FoodDetectorNode(Node):

    def __init__(self) -> None:
        super().__init__('food_detector_node')

        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('model_path', 'yolo11n.pt')
        self.declare_parameter('confidence_threshold', 0.4)
        # Type-only declarations for array parameters:
        # `declare_parameter(name, value, descriptor)` in rclpy Humble lets the
        # *value*'s inferred type win over the descriptor. An empty Python list
        # `[]` is inferred as BYTE_ARRAY -- which then rejects any
        # STRING_ARRAY/INTEGER_ARRAY override from launch/CLI.
        # `Parameter.Type.X` declares the type with NO default, bypassing
        # value-inference entirely. We supply our own defaults below in code.
        self.declare_parameter('food_class_ids', Parameter.Type.INTEGER_ARRAY)
        self.declare_parameter('vocabulary', Parameter.Type.STRING_ARRAY)
        self.declare_parameter('show_window', True)
        self.declare_parameter('window_name', 'Food Detection')
        self.declare_parameter('device', 'cpu')

        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self._conf = self.get_parameter('confidence_threshold').get_parameter_value().double_value
        # Type-only declarations are "uninitialized" until something sets them.
        # No override -> use sensible defaults.
        self._food_ids = set(
            self._get_array_param('food_class_ids', 'integer_array_value', COCO_FOOD_CLASS_IDS)
        )
        vocabulary = list(
            self._get_array_param('vocabulary', 'string_array_value', [])
        )
        self._show_window = self.get_parameter('show_window').get_parameter_value().bool_value
        self._window_name = self.get_parameter('window_name').get_parameter_value().string_value
        self._device = self.get_parameter('device').get_parameter_value().string_value

        self._bridge = CvBridge()
        self._open_vocab_mode = bool(vocabulary)

        # If user supplied a vocabulary but didn't override model_path away from
        # the COCO default, swap to YOLO-World automatically. This avoids the
        # silent failure mode where set_classes() is called on a model that
        # doesn't support it.
        if self._open_vocab_mode and model_path == 'yolo11n.pt':
            model_path = DEFAULT_OPEN_VOCAB_MODEL
            self.get_logger().info(
                f'vocabulary is set -> auto-switching model to {model_path}',
            )

        self.get_logger().info(f'Loading model: {model_path} (device={self._device})')
        self._model = YOLO(model_path)

        if self._open_vocab_mode:
            try:
                self._model.set_classes(vocabulary)
            except AttributeError as e:
                raise RuntimeError(
                    f"Model '{model_path}' does not support open-vocabulary "
                    f"set_classes(). Use a YOLO-World model (e.g. "
                    f"'{DEFAULT_OPEN_VOCAB_MODEL}') or clear the `vocabulary` "
                    f"parameter."
                ) from e
            # YOLO-World rebuilds .names to match the vocabulary, indexed 0..N-1.
            self._class_names: dict[int, str] = {i: name for i, name in enumerate(vocabulary)}
            self.get_logger().info(
                f'Open-vocabulary mode: {len(vocabulary)} classes -> {vocabulary}'
            )
        else:
            self._class_names = self._model.names
            if self._food_ids:
                food_names = [self._class_names.get(i, f'id={i}') for i in sorted(self._food_ids)]
                self.get_logger().info(
                    f'COCO mode: filtering to {len(self._food_ids)} classes -> {food_names}'
                )
            else:
                self.get_logger().info('COCO mode: no class filter -- publishing all detections')

        # BEST_EFFORT + depth 1 = latest-frame-wins, drop stale frames.
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self._sub = self.create_subscription(
            Image, image_topic, self._image_cb, sensor_qos,
        )
        self._annotated_pub = self.create_publisher(
            Image, '/perception/food_detections/image', 10,
        )
        self._detections_pub = self.create_publisher(
            Detection2DArray, '/perception/food_detections', 10,
        )

        self.get_logger().info(f'Subscribed to {image_topic}, ready for inference')

    def _get_array_param(self, name: str, value_field: str, default):
        """Read an array parameter, returning `default` if uninitialized.

        Used with type-only declarations (Parameter.Type.X) where rclpy
        won't assign a default value. This keeps `ros2 run` (no args) and
        `ros2 launch` (always overrides) both working with the same code.
        """
        try:
            return getattr(
                self.get_parameter(name).get_parameter_value(), value_field,
            )
        except ParameterUninitializedException:
            return default

    def _image_cb(self, msg: Image) -> None:
        try:
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn(f'cv_bridge failed: {e}')
            return

        # `verbose=False` silences ultralytics per-frame stdout spam.
        results = self._model.predict(
            frame,
            conf=self._conf,
            device=self._device,
            verbose=False,
        )
        result = results[0]

        annotated, detection_array = self._build_outputs(frame, result, msg.header)

        self._annotated_pub.publish(
            self._bridge.cv2_to_imgmsg(annotated, encoding='bgr8'),
        )
        self._detections_pub.publish(detection_array)

        if self._show_window:
            cv2.imshow(self._window_name, annotated)
            # Required to pump the GUI event loop. 1ms is enough.
            cv2.waitKey(1)

    def _build_outputs(
        self,
        frame: np.ndarray,
        result,
        header,
    ) -> tuple[np.ndarray, Detection2DArray]:
        annotated = frame.copy()
        det_array = Detection2DArray()
        det_array.header = header

        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return annotated, det_array

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clses = boxes.cls.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), conf, cls_id in zip(xyxy, confs, clses):
            # In open-vocab mode every detection is by-construction in the
            # user's vocabulary, so the COCO id filter doesn't apply.
            if not self._open_vocab_mode and self._food_ids and cls_id not in self._food_ids:
                continue

            label = self._class_names.get(int(cls_id), str(cls_id))
            self._draw_box(annotated, x1, y1, x2, y2, label, conf)
            det_array.detections.append(
                self._make_detection(x1, y1, x2, y2, label, conf, header),
            )

        return annotated, det_array

    @staticmethod
    def _draw_box(
        img: np.ndarray,
        x1: float, y1: float, x2: float, y2: float,
        label: str, conf: float,
    ) -> None:
        p1 = (int(x1), int(y1))
        p2 = (int(x2), int(y2))
        cv2.rectangle(img, p1, p2, (0, 255, 0), 2)
        text = f'{label} {conf:.2f}'
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (p1[0], p1[1] - th - 6), (p1[0] + tw + 4, p1[1]), (0, 255, 0), -1)
        cv2.putText(
            img, text, (p1[0] + 2, p1[1] - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
        )

    @staticmethod
    def _make_detection(
        x1: float, y1: float, x2: float, y2: float,
        label: str, conf: float, header,
    ) -> Detection2D:
        det = Detection2D()
        det.header = header
        # vision_msgs 4.x: BoundingBox2D.center is a vision_msgs/Pose2D where
        # x/y live inside a nested Point2D `position` field (NOT directly on
        # the Pose2D like the older geometry_msgs/Pose2D layout).
        det.bbox.center.position.x = float((x1 + x2) / 2.0)
        det.bbox.center.position.y = float((y1 + y2) / 2.0)
        det.bbox.center.theta = 0.0
        det.bbox.size_x = float(x2 - x1)
        det.bbox.size_y = float(y2 - y1)

        hypothesis = ObjectHypothesisWithPose()
        # vision_msgs in Humble uses string class_id.
        hypothesis.hypothesis.class_id = label
        hypothesis.hypothesis.score = float(conf)
        det.results.append(hypothesis)
        return det

    def destroy_node(self) -> bool:
        if self._show_window:
            cv2.destroyAllWindows()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FoodDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001
            pass


if __name__ == '__main__':
    main()
