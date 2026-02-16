# TODO:
# Camera setup
# Gripper control
# Position control

from pymycobot import MyCobot280
from pymycobot import PI_PORT, PI_BAUD 
import time
import cv2

class MyCobotManager:
    def __init__(self):

        # Pre-set poses
        self.DUCK_DETECT_POSE = [170.5, -58.3, 182.7, 180, -5, -45]
        self.HUMAN_DETECT_POSE = [86.6, -121.2, 389.9, -80.09, 42.7, -105.22]

        # Initialize MyCobot280
        self.mc = MyCobot280(PI_PORT, PI_BAUD)
        self.SPEED = 90 # 1 ~100
        self.MODE = 1

        # more responsive in refresh mode
        if self.mc.get_fresh_mode() != 1:
            self.mc.set_fresh_mode(1)

    def gripper_open(self):
        self.mc.set_gripper_state(0, 80)

    def gripper_close(self):
        self.mc.set_gripper_state(1, 80)

    def move_to_pose(self, pose):
        self.mc.send_coords(pose, self.SPEED, self.MODE)