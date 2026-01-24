import cv2
import numpy as np
from pymycobot.mycobot280 import MyCobot280
from pymycobot import PI_PORT, PI_BAUD
import time

frame_count = 0

faceClassifier = cv2.CascadeClassifier("./FaceDetection/haarcascade_frontalface_default.xml")
cap = cv2.VideoCapture(0)

# Reduce resolution for better X11 forwarding performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Give camera time to initialize
time.sleep(2)

for _ in range(5):
    cap.read()


if not cap.isOpened():
    print("Camera cannot be accessed")
    exit()

# Initialize MyCobot280
mc = MyCobot280(PI_PORT, PI_BAUD)

if mc.get_fresh_mode() != 1:
    mc.set_fresh_mode(1)

CAM_POSE = [-72.9, -159.1, 363.3, -122.86, 44.33, 160.6]
INCREMENT = 20
SPEED = 50
MODE = 1

print(mc.get_angles())

mc.send_coords(CAM_POSE, SPEED, MODE)

qPressed = False
face_center = (0, 0)
while (qPressed == False):
    ret, frame = cap.read()

    if ret == True:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceClassifier.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=2)
    

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        face_center = ((x + w) / 2, ((y + h) / 2))

    text = f"Num face:{len(faces)} coord: {face_center}"        

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, (0, 30), font, 1, (255, 0, 0), 1)

    frame_count += 1
    if frame_count % 3 == 0:
        cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        qPressed = True
        break


cap.release()
cv2.destroyAllWindows()
