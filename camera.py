import cv2


class Camera:
    """Single source for camera images. Feed frames to ducky_detector or face_detector."""

    def __init__(self, width=640, height=480, device_id=0):
        self.width = int(width)
        self.height = int(height)
        self._cap = cv2.VideoCapture(device_id)
        if not self._cap.isOpened():
            raise RuntimeError(f"Camera {device_id} could not be opened")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self):
        """Read next frame. Returns (success: bool, frame: np.ndarray or None)."""
        return self._cap.read()

    def is_opened(self):
        """Return True if the camera is open and ready to read."""
        return self._cap.isOpened()

    def release(self):
        """Release the camera. Safe to call multiple times."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

if __name__ == "__main__":
    camera = Camera(320, 240)
    while True:
        if camera.is_opened():
            ret, frame = camera.read()
            cv2.imshow("frame", frame)
            
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break
    camera.release()