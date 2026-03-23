# examples from:
# HSV color detect: https://medium.com/@VinitKumarGupta/color-detection-in-opencv-a-hands-on-project-to-master-hsv-filtering-5fa9fd928561

import cv2
import numpy as np

CAM_IDX = 0

# initialize lower, upper bound of HSV
LH_INIT = 17
LS_INIT = 110
LV_INIT = 50
HH_INIT = 30
HS_INIT = 255
HV_INIT = 255

## create window placeholder and spawn at specific locations for ease of debugging
cv2.namedWindow("trackbars", cv2.WINDOW_NORMAL)
cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("hsv", cv2.WINDOW_NORMAL)
cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
cv2.namedWindow("res", cv2.WINDOW_NORMAL)

cv2.moveWindow("trackbars", 0, 0)
cv2.moveWindow("frame", 200, 50)
cv2.moveWindow("hsv", 300, 100)
cv2.moveWindow("mask", 400, 200)
cv2.moveWindow("res", 500, 300)

def empty(x):
    pass

cv2.namedWindow("trackbars")
# cv2.resizeWindow("trackbars", 640, 240)
cv2.createTrackbar("LH", "trackbars", 0, 179, empty)
cv2.createTrackbar("LS", "trackbars", 0, 255, empty)
cv2.createTrackbar("LV", "trackbars", 0, 255, empty)
cv2.createTrackbar("HH", "trackbars", 0, 179, empty)
cv2.createTrackbar("HS", "trackbars", 0, 255, empty)
cv2.createTrackbar("HV", "trackbars", 0, 255, empty)

cv2.setTrackbarPos("LH", "trackbars", LH_INIT)
cv2.setTrackbarPos("LS", "trackbars", LS_INIT)
cv2.setTrackbarPos("LV", "trackbars", LV_INIT)
cv2.setTrackbarPos("HH", "trackbars", HH_INIT)
cv2.setTrackbarPos("HS", "trackbars", HS_INIT)
cv2.setTrackbarPos("HV", "trackbars", HV_INIT)

# connect camera stream
cam = cv2.VideoCapture(CAM_IDX)
frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

while True:
    ret, frame = cam.read()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    l_h = cv2.getTrackbarPos("LH", "trackbars")
    l_s = cv2.getTrackbarPos("LS", "trackbars")
    l_v = cv2.getTrackbarPos("LV", "trackbars")
    h_h = cv2.getTrackbarPos("HH", "trackbars")
    h_s = cv2.getTrackbarPos("HS", "trackbars")
    h_v = cv2.getTrackbarPos("HV", "trackbars")

    # create a given numpy array
    l_b = np.array([l_h, l_s, l_v])
    u_b = np.array([h_h, h_s, h_v])

    # create a mask
    mask = cv2.inRange(hsv, l_b, u_b)
    res = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("frame", frame)
    cv2.imshow("hsv", hsv)
    cv2.imshow("mask", mask)
    cv2.imshow("res", res)

    if cv2.waitKey(10) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()