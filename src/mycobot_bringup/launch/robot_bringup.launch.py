"""
Bring up the myCobot 280 Pi driver, gripper, and camera nodes.

Usage:
  ros2 launch mycobot_bringup robot_bringup.launch.py
  ros2 launch mycobot_bringup robot_bringup.launch.py robot_ip:=192.168.1.169
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    robot_ip_arg = DeclareLaunchArgument(
        'robot_ip', default_value='192.168.1.169',
    )
    robot_port_arg = DeclareLaunchArgument(
        'robot_port', default_value='9000',
    )
    camera_port_arg = DeclareLaunchArgument(
        'camera_port', default_value='8080',
    )

    robot_ip = LaunchConfiguration('robot_ip')
    robot_port = LaunchConfiguration('robot_port')
    camera_port = LaunchConfiguration('camera_port')

    description_dir = get_package_share_directory('mycobot_description')
    xacro_file = os.path.join(description_dir, 'urdf', 'mycobot_280pi.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
    )

    hardware_node = Node(
        package='mycobot_driver',
        executable='mycobot_hardware_node',
        name='mycobot_hardware_node',
        parameters=[{
            'robot_ip': robot_ip,
            'robot_port': robot_port,
            'publish_rate': 20.0,
            'default_speed': 80,
        }],
        output='screen',
    )

    gripper_node = Node(
        package='mycobot_driver',
        executable='gripper_node',
        name='gripper_node',
        parameters=[{
            'robot_ip': robot_ip,
            'robot_port': robot_port,
            'gripper_speed': 80,
        }],
        output='screen',
    )

    camera_node = Node(
        package='mycobot_camera',
        executable='camera_node',
        name='camera_node',
        parameters=[{
            'camera_url': PythonExpression([
                "'http://'", " + '", robot_ip,
                "' + ':'", " + '", camera_port,
                "' + '/?action=stream'",
            ]),
            'frame_rate': 30.0,
        }],
        output='screen',
    )

    return LaunchDescription([
        robot_ip_arg,
        robot_port_arg,
        camera_port_arg,
        robot_state_publisher,
        hardware_node,
        gripper_node,
        camera_node,
    ])
