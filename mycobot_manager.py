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
        # self.DUCK_DETECT_POSE = [170.5, -58.3, 190.7, 180, -5, -45]
        self.DUCK_DETECT_POSE = [115.5, -56.2, 284.6, -178.73, -4.05, -39.3]
        self.HUMAN_DETECT_POSE = [86.6, -121.2, 389.9, -80.09, 42.7, -105.22]

        self.current_pose = None

        # Initialize MyCobot280
        self.mc = MyCobot280(PI_PORT, PI_BAUD)
        self.SPEED = 100 # 1 ~100
        self.MODE = 1

        # more responsive in refresh mode
        if self.mc.get_fresh_mode() != 1:
            self.mc.set_fresh_mode(1)

        # get current pose
        self.current_pose = self.mc.get_coords()

    def gripper_open(self):
        self.mc.set_gripper_state(0, 80)

    def gripper_close(self):
        self.mc.set_gripper_state(1, 80)

    def move_to_pose(self, pose):
        self.mc.send_coords(pose, self.SPEED, self.MODE)
        
        # naive way of update x, y without verifying...
        # self.current_pose[0] = pose[0]
        # self.current_pose[1] = pose[1]

        self.set_current_pose()

    def set_current_pose(self):
        curr_pose = self.mc.get_coords()
        # only update x, y
        self.current_pose[0] = curr_pose[0]
        self.current_pose[1] = curr_pose[1]
        # maintain same camera orientation and z
        self.current_pose[2] = self.DUCK_DETECT_POSE[2]
        self.current_pose[3] = self.DUCK_DETECT_POSE[3]
        self.current_pose[4] = self.DUCK_DETECT_POSE[4]
        self.current_pose[5] = self.DUCK_DETECT_POSE[5]

    def get_current_pose(self):
        return self.mc.get_coords()