## TODO
# - [ ] detect ducky
# - [ ] move and grab ducky
# - [ ] turn into face detection mode

from mycobot_manager import MyCobotManager
from ducky_detector import DuckyDetector
import time
import cv2

def test_mycobot():
    mycobot = MyCobotManager()
    mycobot.gripper_open()
    time.sleep(0.3)
    mycobot.gripper_close()
    time.sleep(0.3)
    mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
    time.sleep(0.3)
    mycobot.move_to_pose(mycobot.HUMAN_DETECT_POSE)
    time.sleep(0.3)
    mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
    time.sleep(0.3)

def test_ducky_detector():
    ducky_detector = DuckyDetector()
    ducky_detector.run()

def main():
    pass

if __name__ == "__main__":
    # test_mycobot()
    # test_camera()
    test_ducky_detector()
    # main()