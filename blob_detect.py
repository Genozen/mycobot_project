# examples from:
# Blob detection: https://karooza.net/blob-detection-and-tracking

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

lower_bound_orange = np.array([LH_INIT, LS_INIT, LV_INIT])
upper_bound_orange = np.array([HH_INIT, HS_INIT, HV_INIT])

font = cv2.FONT_HERSHEY_SIMPLEX

# Adjust detection parameters
params = cv2.SimpleBlobDetector_Params()
 
# Change thresholds
params.minThreshold = 0;
params.maxThreshold = 100;
 
# Filter by Area
params.filterByArea = True
params.minArea = 400
params.maxArea = 20000
 
# Filter by Circularity
params.filterByCircularity = False
params.minCircularity = 0.1
 
# Filter by Convexity
params.filterByConvexity = False
params.minConvexity = 0.5
 
# Filter by Inertia
params.filterByInertia = False
params.minInertiaRatio = 0.5

## create window placeholder and spawn at specific locations for ease of debugging
# cv2.namedWindow("trackbars", cv2.WINDOW_NORMAL)
cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("hsv", cv2.WINDOW_NORMAL)
cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
cv2.namedWindow("res", cv2.WINDOW_NORMAL)

# cv2.moveWindow("trackbars", 0, 0)
cv2.moveWindow("frame", 200, 50)
cv2.moveWindow("hsv", 300, 100)
cv2.moveWindow("mask", 400, 200)
cv2.moveWindow("res", 500, 300)

# connect camera stream
cam = cv2.VideoCapture(CAM_IDX)
frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

while True:
    ret, frame = cam.read()

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # apply HSV threshold
    mask = cv2.inRange(hsv, lower_bound_orange, upper_bound_orange)

    # erode and dilate
    mask = cv2.erode(mask, None, iterations=3)
    mask = cv2.dilate(mask, None, iterations=3)
    
	# Detect blobs
    detector = cv2.SimpleBlobDetector_create(params)
	
    # Invert the mask
    reversemask = 255-mask

    # Run blob detection
    keypoints = detector.detect(reversemask)

    # Get the number of blobs found
    blobCount = len(keypoints)

    # Write the number of blobs found
    text = "Count=" + str(blobCount) 
    cv2.putText(frame, text, (5,25), font, 1, (0, 255, 0), 2)


    if blobCount > 0:
        # Write X position of first blob
        blob_x = keypoints[0].pt[0]
        text2 = "X=" + "{:.2f}".format(blob_x )
        cv2.putText(frame, text2, (5,50), font, 1, (0, 255, 0), 2)

        # Write Y position of first blob
        blob_y = keypoints[0].pt[1]
        text3 = "Y=" + "{:.2f}".format(blob_y)
        cv2.putText(frame, text3, (5,75), font, 1, (0, 255, 0), 2)        

        # Write Size of first blob
        blob_size = keypoints[0].size
        text4 = "S=" + "{:.2f}".format(blob_size)
        cv2.putText(frame, text4, (5,100), font, 1, (0, 255, 0), 2)    

        # Draw circle to indicate the blob
        cv2.circle(frame, (int(blob_x),int(blob_y)), int(blob_size / 2), (0, 255, 0), 2) 
    
    
    # res = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("frame", frame)
    cv2.imshow("hsv", hsv)
    cv2.imshow("mask", mask)
    # cv2.imshow("res", res)

    if cv2.waitKey(10) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()