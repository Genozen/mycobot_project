## TODO
# - [ ] detect ducky
# - [ ] move and grab ducky
# - [ ] turn into face detection mode

from mycobot_manager import MyCobotManager
from ducky_detector import DuckyDetector
from face_detector import FaceDetector
from camera import Camera
import time
import cv2


DUCK_CENTER = (230, 230) # x, y of the center coordinate form the camera reading
DISTANCE_THRESHOLD = 5
INCREMENT = 2
PIXEL_TO_MM_RATIO = 0.497 # mm / px
FACE_CENTER = (320, 240)   # target pixel center — tuned for 320x240 from mediapipe_face_detect.py
CENTER_THRESHOLD = 60      # deadband in pixels
CENTER_SHIFT = 60          # camera offset from gripper
cv2.namedWindow("frame", cv2.WINDOW_NORMAL)

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

    camera = Camera(width=640, height=480)
    
    ducky_detector = DuckyDetector()
    # ducky_detector.start()  # Non-blocking start in separate thread
    face_detector = FaceDetector()

    mycobot.move_to_pose(mycobot.HUMAN_DETECT_POSE)

    display_counter = 0 
    try:
        while camera.is_opened():

            # Display frames (must be called from main thread for OpenCV GUI)
            # ducky_detector.display_frames()
            
            # mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
            # time.sleep(3.0) # wait for robot movement to settle
            
            print("Scanning for ducky...")
            ret, frame = camera.read()
            if not ret:
                break

            # ducky_detector.detect(frame)

            # # Get ducky position
            # ducky_x, ducky_y = ducky_detector.get_ducky_position()
            # if ducky_x is not None and ducky_y is not None:
            #     print(f"Ducky at: ({ducky_x:.2f}, {ducky_y:.2f})")

            #     pix_dist_x = ducky_x - DUCK_CENTER[0]
            #     robot_dist_x = pix_dist_x * PIXEL_TO_MM_RATIO
            #     print("pix dist:", pix_dist_x)
            #     print("robot dist:", robot_dist_x)
            #     new_pose = mycobot.current_pose.copy()
            #     new_pose[0] += robot_dist_x

            #     pix_dist_y = ducky_y - DUCK_CENTER[1]
            #     robot_dist_y = pix_dist_y * PIXEL_TO_MM_RATIO
            #     print("pix dist:", pix_dist_y)
            #     print("robot dist:", robot_dist_y)
            #     new_pose[1] -= robot_dist_y
            #     new_pose[2] = 140.0
            #     print("move to: ", new_pose)
            #     mycobot.move_to_pose(new_pose)
            #     time.sleep(0.5)
            #     mycobot.gripper_close()

            #     # move upwards to prevent diagonal movement which drops the ducky
            #     above_ducky_pose = new_pose.copy()
            #     above_ducky_pose[2] += 50
            #     mycobot.move_to_pose(above_ducky_pose)
            #     time.sleep(1.0)

            #     mycobot.move_to_pose(mycobot.DUCK_DETECT_POSE)
            #     mycobot.move_to_pose(above_ducky_pose)
            #     mycobot.move_to_pose(new_pose)
            #     mycobot.gripper_open()

            ## FACE DETECTION MODE
            # mycobot.move_to_pose(mycobot.HUMAN_DETECT_POSE)
            # time.sleep(3.0) # wait for robot movement to settle
            

            print("Scanning for human...")
            ret, frame = camera.read()
            if not ret:
                break

            cv2.imshow("frame", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            face_detector.detect(frame)
            face_x, face_y = face_detector.get_face_position()
            # if face_x is not None and face_y is not None:
            #     print(f"Human at: ({face_x:.2f}, {face_y:.2f})")

            if face_x is not None and face_y is not None:
                print(f"Human at: ({face_x}, {face_y})")

                dist_x = abs(face_x - (FACE_CENTER[0] + CENTER_SHIFT + CENTER_THRESHOLD))
                if face_x > FACE_CENTER[0] + CENTER_SHIFT + CENTER_THRESHOLD:
                    mycobot.mc.jog_increment_angle(joint_id=1, increment=-dist_x / 7, speed=100, _async=True)
                    print("moving right")
                elif face_x < FACE_CENTER[0] + CENTER_SHIFT - CENTER_THRESHOLD:
                    mycobot.mc.jog_increment_angle(joint_id=1, increment=dist_x / 7, speed=100, _async=True)
                    print("moving left")

                dist_y = abs(face_y - (FACE_CENTER[1] + CENTER_THRESHOLD))
                if face_y > FACE_CENTER[1] + CENTER_THRESHOLD:
                    mycobot.mc.jog_increment_angle(joint_id=4, increment=-dist_y / 7, speed=100, _async=True)
                    print("moving up")
                elif face_y < FACE_CENTER[1] - CENTER_THRESHOLD:
                    mycobot.mc.jog_increment_angle(joint_id=4, increment=dist_y / 7, speed=100, _async=True)
                    print("moving down")
                time.sleep(0.1)



    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # ducky_detector.stop()
        cv2.destroyAllWindows()
        camera.release()

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
