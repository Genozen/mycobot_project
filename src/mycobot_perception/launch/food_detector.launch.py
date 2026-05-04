"""
Launch the YOLO food-detection node.

Subscribes to a sensor_msgs/Image topic (default /camera/image_raw),
runs inference, and:
  - shows a CV2 window with bounding boxes
  - publishes annotated frames on /perception/food_detections/image
  - publishes structured detections on /perception/food_detections

Two modes:
  - COCO mode (vocabulary:='[]'): YOLOv11 + 10 COCO food classes.
  - Open-vocab mode (any vocabulary): YOLO-World, detect arbitrary nouns.

The default below uses YOLO-World with a kitchen-friendly vocabulary
(vegetables, fruits, pizza, fries, ketchup, eggs, bread, milk, cookies,
cheese). Override `vocabulary:=...` to change it, or set it to `[]` to
fall back to the lighter-weight COCO model.

Usage:
  ros2 launch mycobot_perception food_detector.launch.py
  ros2 launch mycobot_perception food_detector.launch.py show_window:=false
  ros2 launch mycobot_perception food_detector.launch.py vocabulary:='["apple","banana"]'
  ros2 launch mycobot_perception food_detector.launch.py vocabulary:='[]'   # COCO mode
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


# Default open-vocabulary list, derived from the user's kitchen items.
# YOLO-World works best with concrete, common nouns -- so "vegetables"
# and "fruits" are split into specific items below.
DEFAULT_VOCABULARY = [
    'broccoli', 'carrot', 'tomato', 'lettuce', 'bell pepper', 'cucumber',
    'apple', 'banana', 'orange', 'strawberry', 'grape', 'lemon',
    'pizza', 'french fries', 'ketchup bottle',
    'egg', 'bread', 'milk carton', 'cookie', 'cheese',
]


def generate_launch_description() -> LaunchDescription:
    image_topic_arg = DeclareLaunchArgument(
        'image_topic',
        default_value='/camera/image_raw',
        description='sensor_msgs/Image topic to subscribe to',
    )
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolo11n.pt',
        description=(
            'Ultralytics model name or path to .pt. Auto-switches to '
            'yolov8s-worldv2.pt when `vocabulary` is non-empty.'
        ),
    )
    confidence_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.1',
        description=(
            'Minimum confidence to keep a detection. YOLO-World tends to '
            'produce lower scores than COCO YOLO -- 0.1-0.2 works well.'
        ),
    )
    vocabulary_arg = DeclareLaunchArgument(
        'vocabulary',
        # YAML-list literal -- launch will pass this through as a string array.
        default_value=str(DEFAULT_VOCABULARY).replace("'", '"'),
        description=(
            'Open-vocabulary class names for YOLO-World. '
            'Set to `[]` to use the COCO model + food_class_ids filter.'
        ),
    )
    show_window_arg = DeclareLaunchArgument(
        'show_window',
        default_value='true',
        description='Show OpenCV preview window. Set false for headless.',
    )
    device_arg = DeclareLaunchArgument(
        'device',
        default_value='cpu',
        description='Inference device: "cpu", "0" (first GPU), "cuda:0", etc.',
    )

    food_detector_node = Node(
        package='mycobot_perception',
        executable='food_detector_node',
        name='food_detector_node',
        parameters=[{
            'image_topic': LaunchConfiguration('image_topic'),
            'model_path': LaunchConfiguration('model_path'),
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'vocabulary': LaunchConfiguration('vocabulary'),
            'show_window': LaunchConfiguration('show_window'),
            'device': LaunchConfiguration('device'),
        }],
        output='screen',
    )

    return LaunchDescription([
        image_topic_arg,
        model_path_arg,
        confidence_arg,
        vocabulary_arg,
        show_window_arg,
        device_arg,
        food_detector_node,
    ])
