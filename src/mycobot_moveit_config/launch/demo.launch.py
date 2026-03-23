"""
MoveIt2 demo launch file for myCobot 280 Pi.

Launches robot_state_publisher, MoveIt2 move_group, and RViz2 with
the MotionPlanning plugin for interactive drag-and-plan.
"""

import os
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
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
        robot_state_publisher,
        move_group_node,
        rviz_node,
    ])
