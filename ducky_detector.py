import numpy as np
import cv2

# preset cv2 windows
font = cv2.FONT_HERSHEY_SIMPLEX

cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
cv2.namedWindow("hsv", cv2.WINDOW_NORMAL)
cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
cv2.namedWindow("res", cv2.WINDOW_NORMAL)

cv2.moveWindow("frame", 200, 50)
cv2.moveWindow("hsv", 300, 100)
cv2.moveWindow("mask", 400, 200)
cv2.moveWindow("res", 500, 300)


class DuckyDetector:
    def __init__(self):
        
        # HSV for ducky yellow
        self.lower_bound_yellow = np.array([17, 110, 50])
        self.upper_bound_yellow = np.array([30, 255, 255])

        # Blob detector parameters
        self.params = cv2.SimpleBlobDetector_Params()
        self.params.filterByArea = True
        self.params.minArea = 400
        self.params.maxArea = 20000
        self.params.filterByCircularity = False
        self.params.minCircularity = 0.1
        self.params.filterByConvexity = False
        self.params.minConvexity = 0.5
        self.params.filterByInertia = False
        self.params.minInertiaRatio = 0.5
        self.detector = cv2.SimpleBlobDetector_create(self.params)


        self.CAM_IDX = 0
        # connect camera stream
        self.cam = cv2.VideoCapture(self.CAM_IDX)
        self.frame_width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # ducky position
        self.ducky_x = None
        self.ducky_y = None
        self.ducky_size = None

    def run(self):
        while True:
            ret, frame = self.cam.read()
            if not ret:
                break
            self._detect(frame)
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break
        self.cam.release()
        cv2.destroyAllWindows()

    def _detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_bound_yellow, self.upper_bound_yellow)
        mask = cv2.erode(mask, None, iterations=3)
        mask = cv2.dilate(mask, None, iterations=3)
        reversemask = 255-mask

        keypoints = self.detector.detect(reversemask)
        blobCount = len(keypoints)

        
        if blobCount > 0:
            self.ducky_x = keypoints[0].pt[0]
            self.ducky_y = keypoints[0].pt[1]
            self.ducky_size = keypoints[0].size
        else:
            self.ducky_x = None
            self.ducky_y = None
            self.ducky_size = None

        if blobCount > 0:
            # draw on cv window
            text = "Count=" + str(blobCount) 
            cv2.putText(frame, text, (5,25), font, 1, (0, 255, 0), 2)
            text2 = "X=" + "{:.2f}".format(self.ducky_x )
            cv2.putText(frame, text2, (5,50), font, 1, (0, 255, 0), 2)
            text3 = "Y=" + "{:.2f}".format(self.ducky_y)
            cv2.putText(frame, text3, (5,75), font, 1, (0, 255, 0), 2)
            text4 = "S=" + "{:.2f}".format(self.ducky_size)
            cv2.putText(frame, text4, (5,100), font, 1, (0, 255, 0), 2)
            cv2.circle(frame, (int(self.ducky_x),int(self.ducky_y)), int(self.ducky_size / 2), (0, 255, 0), 2) 

        cv2.imshow("frame", frame)
        cv2.imshow("hsv", hsv)
        cv2.imshow("mask", mask)

    def get_ducky_position(self):
        return self.ducky_x, self.ducky_y
