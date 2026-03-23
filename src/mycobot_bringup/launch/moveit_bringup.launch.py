"""
Full MoveIt2 bringup for myCobot 280 Pi.

Launches:
  - robot_state_publisher (publishes URDF TF tree)
  - mycobot_hardware_node (arm joint states + trajectory action + gripper service)
  - camera_node (MJPEG stream -> sensor_msgs/Image for RViz2)
  - move_group (MoveIt2 motion planning via OMPL/RRTConnect)
  - rviz2 (visualization with MotionPlanning panel)

Usage:
  ros2 launch mycobot_bringup moveit_bringup.launch.py
  ros2 launch mycobot_bringup moveit_bringup.launch.py robot_ip:=192.168.1.169
"""

import os
import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def load_yaml(package_name, file_path):
    full_path = os.path.join(get_package_share_directory(package_name), file_path)
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)


def generate_launch_description():
    robot_ip_arg = DeclareLaunchArgument('robot_ip', default_value='192.168.1.169')
    robot_port_arg = DeclareLaunchArgument('robot_port', default_value='9000')
    camera_port_arg = DeclareLaunchArgument('camera_port', default_value='8080')

    robot_ip = LaunchConfiguration('robot_ip')
    robot_port = LaunchConfiguration('robot_port')
    camera_port = LaunchConfiguration('camera_port')

    description_dir = get_package_share_directory('mycobot_description')
    moveit_dir = get_package_share_directory('mycobot_moveit_config')
    xacro_file = os.path.join(description_dir, 'urdf', 'mycobot_280pi.urdf.xacro')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    with open(os.path.join(moveit_dir, 'config', 'mycobot_280pi.srdf'), 'r') as f:
        robot_description_semantic = f.read()

    kinematics_yaml = load_yaml('mycobot_moveit_config', 'config/kinematics.yaml')
    joint_limits_yaml = load_yaml('mycobot_moveit_config', 'config/joint_limits.yaml')
    controllers_yaml = load_yaml('mycobot_moveit_config', 'config/moveit_controllers.yaml')

    ompl_yaml = load_yaml('mycobot_moveit_config', 'config/ompl_planning.yaml')
    planning_pipelines_config = {
        'planning_pipelines': ['ompl'],
        'default_planning_pipeline': 'ompl',
        'ompl': ompl_yaml,
    }

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
            'frame_rate': 15.0,
        }],
        output='screen',
    )

    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'robot_description_semantic': robot_description_semantic,
                'robot_description_planning': joint_limits_yaml,
                'use_sim_time': False,
                'trajectory_execution.allowed_execution_duration_scaling': 4.0,
                'trajectory_execution.allowed_goal_duration_margin': 10.0,
                'trajectory_execution.execution_duration_monitoring': False,
            },
            kinematics_yaml,
            controllers_yaml,
            planning_pipelines_config,
        ],
    )

    obstacles_file = os.path.join(moveit_dir, 'config', 'obstacles.yaml')

    scene_objects_node = Node(
        package='mycobot_driver',
        executable='scene_objects',
        name='scene_objects',
        parameters=[{'obstacles_file': obstacles_file}],
        output='screen',
    )

    rviz_config = os.path.join(moveit_dir, 'rviz', 'moveit.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[
            {
                'robot_description': robot_description,
                'robot_description_semantic': robot_description_semantic,
            },
            kinematics_yaml,
            planning_pipelines_config,
        ],
    )

    return LaunchDescription([
        robot_ip_arg,
        robot_port_arg,
        camera_port_arg,
        robot_state_publisher,
        hardware_node,
        camera_node,
        move_group_node,
        scene_objects_node,
        rviz_node,
    ])
