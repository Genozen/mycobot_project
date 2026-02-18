import numpy as np
import cv2
import threading

# preset cv2 windows
font = cv2.FONT_HERSHEY_SIMPLEX

# cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
# cv2.namedWindow("hsv", cv2.WINDOW_NORMAL)
# cv2.namedWindow("mask", cv2.WINDOW_NORMAL)
# cv2.namedWindow("res", cv2.WINDOW_NORMAL)

# cv2.moveWindow("frame", 200, 50)
# cv2.moveWindow("hsv", 300, 100)
# cv2.moveWindow("mask", 400, 200)
# cv2.moveWindow("res", 500, 300)


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

        # self.CAM_IDX = 0
        ## connect camera stream
        # self.cam = cv2.VideoCapture(self.CAM_IDX)
        # self.frame_width = int(self.cam.get(cv2.CAP_PROP_FRAME_WIDTH))
        # self.frame_height = int(self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # ducky position
        self.ducky_x = None
        self.ducky_y = None
        self.ducky_size = None

        # # thread control
        # self.running = False
        # self.thread = None
        
        # # Store latest frames for display (accessed from main thread)
        # self.latest_frame = None
        # self.latest_hsv = None
        # self.latest_mask = None
        # self.frame_lock = threading.Lock()

    # def start(self):
    #     """Start the detector in a separate thread"""
    #     if not self.running:
    #         self.running = True
    #         self.thread = threading.Thread(target=self._run_loop, daemon=True)
    #         self.thread.start()

    # def stop(self):
    #     """Stop the detector thread"""
    #     self.running = False
    #     if self.thread:
    #         self.thread.join()
    #     self.cam.release()
    #     cv2.destroyAllWindows()

    # def _run_loop(self):
    #     """Internal loop that runs in the thread"""
    #     while self.running:
    #         ret, frame = self.cam.read()
    #         if not ret:
    #             break
    #         self._detect(frame)

    def detect(self, frame):
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

        # Draw annotations on frame
        if blobCount > 0:
            text = "Count=" + str(blobCount) 
            cv2.putText(frame, text, (5,25), font, 1, (0, 255, 0), 2)
            text2 = "X=" + "{:.2f}".format(self.ducky_x )
            cv2.putText(frame, text2, (5,50), font, 1, (0, 255, 0), 2)
            text3 = "Y=" + "{:.2f}".format(self.ducky_y)
            cv2.putText(frame, text3, (5,75), font, 1, (0, 255, 0), 2)
            text4 = "S=" + "{:.2f}".format(self.ducky_size)
            cv2.putText(frame, text4, (5,100), font, 1, (0, 255, 0), 2)
            cv2.circle(frame, (int(self.ducky_x),int(self.ducky_y)), int(self.ducky_size / 2), (0, 255, 0), 2) 

        # # Store frames for main thread to display
        # with self.frame_lock:
        #     self.latest_frame = frame.copy()
        #     self.latest_hsv = hsv.copy()
        #     self.latest_mask = mask.copy()

    # def display_frames(self):
    #     """Call this from the main thread to display frames"""
    #     with self.frame_lock:
    #         if self.latest_frame is not None:
    #             cv2.imshow("frame", self.latest_frame)
    #             cv2.imshow("hsv", self.latest_hsv)
    #             cv2.imshow("mask", self.latest_mask)

    def get_ducky_position(self):
        return self.ducky_x, self.ducky_y
