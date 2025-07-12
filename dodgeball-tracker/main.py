import cv2
import numpy as np

cap = cv2.VideoCapture(0)
positions = []

# Define ball color (e.g. red)
lower = np.array([0, 120, 70])
upper = np.array([10, 255, 255])

while True:
    ret, frame = cap.read()
    if not ret: break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if cv2.contourArea(cnt) > 300:
            x, y, w, h = cv2.boundingRect(cnt)
            cx, cy = x + w//2, y + h//2
            positions.append((cx, cy))
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            break  # only track the biggest blob

    # Draw path
    for i in range(1, len(positions)):
        cv2.line(frame, positions[i - 1], positions[i], (255, 0, 0), 2)

    cv2.imshow("Ball Tracker", frame)
    if cv2.waitKey(10) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
