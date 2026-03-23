from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    robot_ip_arg = DeclareLaunchArgument(
        'robot_ip', default_value='192.168.1.160',
        description='IP address of the myCobot 280 Pi',
    )
    robot_port_arg = DeclareLaunchArgument(
        'robot_port', default_value='9000',
        description='TCP port of the pymycobot server',
    )

    robot_ip = LaunchConfiguration('robot_ip')
    robot_port = LaunchConfiguration('robot_port')

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

    return LaunchDescription([
        robot_ip_arg,
        robot_port_arg,
        hardware_node,
        gripper_node,
    ])
