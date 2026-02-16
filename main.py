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
    mycobot = MyCobotManager()
    ducky_detector = DuckyDetector()
    ducky_detector.start()  # Non-blocking start in separate thread

    try:
        while True:
            # Display frames (must be called from main thread for OpenCV GUI)
            ducky_detector.display_frames()
            
            # Get ducky position
            ducky_x, ducky_y = ducky_detector.get_ducky_position()
            if ducky_x is not None and ducky_y is not None:
                print(f"Ducky at: ({ducky_x:.2f}, {ducky_y:.2f})")
            
            # cv2.waitKey MUST be called from main thread for GUI to update
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ducky_detector.stop()

if __name__ == "__main__":
    # test_mycobot()
    # test_camera()
    # test_ducky_detector()
    main()