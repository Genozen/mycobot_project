import cv2
import numpy as np
import time

cap = cv2.VideoCapture(0)

# Reduce resolution for better X11 forwarding performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Give camera time to initialize
time.sleep(2)

# Discard first few frames (they're often black)
for _ in range(5):
    cap.read()

print("Camera initialized. Press 'q' to quit.")
print("Lower resolution (320x240) for better network performance")

frame_count = 0

while(True):
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to grab frame")
        break
    
    # Only display every 3rd frame to reduce lag
    frame_count += 1
    if frame_count % 3 == 0:
        cv2.imshow('frame', frame)
    
    # Debug: print frame stats occasionally
    if cv2.waitKey(100) & 0xFF == ord('d'):  # Increased waitKey for less CPU
        print(f"Frame: min={np.min(frame)}, max={np.max(frame)}, mean={np.mean(frame):.1f}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()