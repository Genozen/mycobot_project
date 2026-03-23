from setuptools import setup
import os
from glob import glob

package_name = 'mycobot_driver'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'pymycobot'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'mycobot_hardware_node = mycobot_driver.mycobot_hardware_node:main',
            'gripper_node = mycobot_driver.gripper_node:main',
        ],
    },
)
