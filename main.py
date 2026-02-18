## TODO
# - [ ] detect ducky
# - [ ] move and grab ducky
# - [ ] turn into face detection mode

from mycobot_manager import MyCobotManager
from ducky_detector import DuckyDetector
import time
import cv2


DUCK_CENTER = (230, 230) # x, y of the center coordinate form the camera reading
DISTANCE_THRESHOLD = 5
INCREMENT = 2
PIXEL_TO_MM_RATIO = 0.497 # mm / px

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
    mycobot.gripper_open()
    mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
    
    ducky_detector = DuckyDetector()
    ducky_detector.start()  # Non-blocking start in separate thread

    try:
        while True:
            # Display frames (must be called from main thread for OpenCV GUI)
            ducky_detector.display_frames()
            
            mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
            print("Scanning for ducky...")
            time.sleep(3.0)

            # Get ducky position
            ducky_x, ducky_y = ducky_detector.get_ducky_position()
            if ducky_x is not None and ducky_y is not None:
                print(f"Ducky at: ({ducky_x:.2f}, {ducky_y:.2f})")

                pix_dist_x = ducky_x - DUCK_CENTER[0]
                robot_dist_x = pix_dist_x * PIXEL_TO_MM_RATIO
                print("pix dist:", pix_dist_x)
                print("robot dist:", robot_dist_x)
                new_pose = mycobot.current_pose.copy()
                new_pose[0] += robot_dist_x

                pix_dist_y = ducky_y - DUCK_CENTER[1]
                robot_dist_y = pix_dist_y * PIXEL_TO_MM_RATIO
                print("pix dist:", pix_dist_y)
                print("robot dist:", robot_dist_y)
                new_pose[1] -= robot_dist_y
                new_pose[2] = 140.0
                print("move to: ", new_pose)
                mycobot.move_to_pose(new_pose)
                mycobot.gripper_close()

                # move upwards to prevent diagonal movement which drops the ducky
                above_ducky_pose = new_pose.copy()
                above_ducky_pose[2] += 50
                mycobot.move_to_pose(above_ducky_pose)
                time.sleep(1.0)

                mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
                mycobot.move_to_pose(above_ducky_pose)
                mycobot.move_to_pose(new_pose)
                mycobot.gripper_open()

            # cv2.waitKey MUST be called from main thread for GUI to update
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ducky_detector.stop()

if __name__ == "__main__":
    print("""
    1. main()
    2. test_mycobot()
    3. test_ducky_detector()
    """)

    # python 3.8 don't have switch/match case statement
    user_input = input("Enter the test number:")
    if user_input == "1":
        main()
    elif user_input == "2":
        test_mycobot()
    elif user_input == "3":
        test_ducky_detector()
    else:
        print("Invalid input")


"""
# ducky pixel (x,y)
ducky_pixel_1 = (348, 247.13)
ducky_pixel_2 = (460, 246)

# ducky robot pose (x, y)
ducky_robot_pose_1 = (176, -54.8)
ducky_robot_pose_2 = (231.7, -42.6)

# calculate the delta between the two points
delta_distance_px = sqrt((348 - 460)^2 + (247.13 - 246)^2) = 112.0
delta_distance_robot = sqrt((176 - 231.7)^2 + (-54.8 - (-42.6))^2) = 55.7

pixel distance to robot distance ratio = 112.0 / 55.7 = 2.01
55.7 / 112.0 = 0.497
"""
