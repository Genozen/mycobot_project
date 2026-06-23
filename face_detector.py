import cv2
import mediapipe as mp


class FaceDetector:
    def __init__(self, model_selection: int = 0, min_detection_confidence: float = 0.5):
        self._mp_face_detection = mp.solutions.face_detection
        self._mp_drawing = mp.solutions.drawing_utils
        self._face_detection = self._mp_face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_detection_confidence,
        )

        self.face_x = None  # pixel x of face center
        self.face_y = None  # pixel y of face center

    def detect(self, frame):
        """Process a BGR frame, annotate it in-place, and update face position."""
        self.face_x = None
        self.face_y = None

        frame.flags.writeable = False
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_detection.process(rgb)
        frame.flags.writeable = True

        if results.detections:
            detection = results.detections[0]  # use the first (most confident) face
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = frame.shape

            self.face_x = int((bboxC.xmin + bboxC.width / 2) * iw)
            self.face_y = int((bboxC.ymin + bboxC.height / 2) * ih)

            self._mp_drawing.draw_detection(frame, detection)

    def get_face_position(self):
        """Return (face_x, face_y) in pixels, or (None, None) if no face detected."""
        return self.face_x, self.face_y

    def close(self):
        self._face_detection.close()
