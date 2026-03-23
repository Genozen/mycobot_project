# https://mediapipe.readthedocs.io/en/latest/solutions/face_detection.html
# sudo pip3 install mediapipe
# center is roughly (150, 130)   
# +x +y is left and down
import cv2
import mediapipe as mp
import time
from pymycobot.mycobot280 import MyCobot280
from pymycobot import PI_PORT, PI_BAUD


## initialize mycobot and move to camera pose
mc = MyCobot280(PI_PORT, PI_BAUD)

if mc.get_fresh_mode() != 1:
    mc.set_fresh_mode(1)

# CAM_POSE = [-72.9, -159.1, 363.3, -122.86, 44.33, 160.6]
CAM_POSE = [86.6, -121.2, 389.9, -80.09, 42.7, -105.22]
INCREMENT = 20
SPEED = 50
MODE = 1

mc.send_coords(CAM_POSE, SPEED, MODE)

## handle face detection
frame_count = 0
face_center = (150, 130) # x, y   (+x +y is left and down)
CENTER_THRESHOLD = 30
CENTER_SHIFT = 30 # camera gets blocked by the gripper a bit

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# For webcam input:
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Give camera time to initialize
time.sleep(2)

# Discard first few frames (they're often black)
for _ in range(5):
    cap.read()

with mp_face_detection.FaceDetection(
    model_selection=0, min_detection_confidence=0.5) as face_detection:
  while cap.isOpened():
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      # If loading a video, use 'break' instead of 'continue'.
      continue

    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_detection.process(image)

    # Draw the face detection annotations on the image.
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    if results.detections:
      for detection in results.detections:
        bboxC = detection.location_data.relative_bounding_box

        ih, iw, _ = image.shape
        center_x_norm = bboxC.xmin + bboxC.width / 2
        center_y_norm = bboxC.ymin + bboxC.height / 2

        center_x_pixel = int(center_x_norm * iw)
        center_y_pixel = int(center_y_norm * ih)
        
        dist_x = 0
        dist_x = abs(center_x_pixel - (face_center[0] + CENTER_SHIFT + CENTER_THRESHOLD))
        if center_x_pixel > face_center[0] + CENTER_SHIFT + CENTER_THRESHOLD:
            mc.jog_increment_angle(joint_id=1, increment=-dist_x/5 , speed=100, _async=True)
        elif center_x_pixel < face_center[0] + CENTER_SHIFT - CENTER_THRESHOLD:
            mc.jog_increment_angle(joint_id=1, increment=dist_x/5, speed=100, _async=True)

        dist_y = 0
        dist_y = abs(center_y_pixel - (face_center[1] + CENTER_THRESHOLD))
        if center_y_pixel > face_center[1] + CENTER_THRESHOLD:
            mc.jog_increment_angle(joint_id=4, increment=-dist_y/5, speed=100, _async=True)
        elif center_y_pixel < face_center[1] - CENTER_THRESHOLD:
            mc.jog_increment_angle(joint_id=4, increment=dist_y/5, speed=100, _async=True)


        mp_drawing.draw_detection(image, detection)

    frame_count += 1
    if frame_count % 5 == 0:
        cv2.imshow('MediaPipe Face Detection', cv2.flip(image, 1)) # Flip the image horizontally for a selfie-view display.
        print(f"Face center: ({center_x_pixel}, {center_y_pixel}) dist: {dist_x}, {dist_y}")

    if cv2.waitKey(5) & 0xFF == 27:
      break
cap.release()