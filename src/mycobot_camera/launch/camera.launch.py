from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_url_arg = DeclareLaunchArgument(
        'camera_url',
        default_value='http://192.168.1.169:8080/?action=stream',
        description='MJPEG stream URL from mjpg-streamer on the Pi',
    )

    camera_node = Node(
        package='mycobot_camera',
        executable='camera_node',
        name='camera_node',
        parameters=[{
            'camera_url': LaunchConfiguration('camera_url'),
            'frame_rate': 30.0,
            'frame_id': 'camera_link',
        }],
        output='screen',
    )

    return LaunchDescription([
        camera_url_arg,
        camera_node,
    ])
