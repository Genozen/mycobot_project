"""
Full MoveIt2 bringup for myCobot 280 Pi.

Launches: driver + gripper + camera + robot_state_publisher + MoveIt2 move_group + RViz2.

Usage:
  ros2 launch mycobot_bringup moveit_bringup.launch.py
  ros2 launch mycobot_bringup moveit_bringup.launch.py robot_ip:=192.168.1.169
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    robot_ip_arg = DeclareLaunchArgument('robot_ip', default_value='192.168.1.169')
    robot_port_arg = DeclareLaunchArgument('robot_port', default_value='9000')

    robot_ip = LaunchConfiguration('robot_ip')
    robot_port = LaunchConfiguration('robot_port')

    description_dir = get_package_share_directory('mycobot_description')
    moveit_dir = get_package_share_directory('mycobot_moveit_config')

    xacro_file = os.path.join(description_dir, 'urdf', 'mycobot_280pi.urdf.xacro')
    srdf_file = os.path.join(moveit_dir, 'config', 'mycobot_280pi.srdf')
    kinematics_file = os.path.join(moveit_dir, 'config', 'kinematics.yaml')
    joint_limits_file = os.path.join(moveit_dir, 'config', 'joint_limits.yaml')
    ompl_file = os.path.join(moveit_dir, 'config', 'ompl_planning.yaml')
    controllers_file = os.path.join(moveit_dir, 'config', 'moveit_controllers.yaml')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    with open(srdf_file, 'r') as f:
        robot_description_semantic = f.read()

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
        }],
        output='screen',
    )

    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            {'robot_description_semantic': robot_description_semantic},
            kinematics_file,
            ompl_file,
            joint_limits_file,
            controllers_file,
            {'use_sim_time': False},
        ],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            {'robot_description_semantic': robot_description_semantic},
            kinematics_file,
        ],
    )

    return LaunchDescription([
        robot_ip_arg,
        robot_port_arg,
        robot_state_publisher,
        hardware_node,
        gripper_node,
        move_group_node,
        rviz_node,
    ])
