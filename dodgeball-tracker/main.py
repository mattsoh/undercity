import cv2
import mediapipe as mp
import time

# Initialize video capture
cap = cv2.VideoCapture(1)

# Initialize mediapipe hand model and drawing utility
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=100)
mpDraw = mp.solutions.drawing_utils

# Time for FPS calculation``
pTime = 0

ball_trajectory = []
last_launch_time = 0

while True:
    success, img = cap.read()
    if not success:
        break

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    h, w, c = img.shape

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                # print(id, cx, cy)
                cv2.circle(img, (cx, cy), 15, (139, 0, 0), cv2.FILLED)
            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

            wrist = handLms.landmark[0]
            middle_mcp = handLms.landmark[9]
            middle_tip = handLms.landmark[12]
            index_tip = handLms.landmark[8]
            ring_tip = handLms.landmark[16]

            # Curved grip detection using finger folding relative to MCP-to-tip straightness
            def distance(a, b):
                return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5

            palm_width = distance(handLms.landmark[5], handLms.landmark[13])
            index_fold = distance(handLms.landmark[6], handLms.landmark[8]) / palm_width
            middle_fold = distance(handLms.landmark[10], handLms.landmark[12]) / palm_width
            ring_fold = distance(handLms.landmark[14], handLms.landmark[16]) / palm_width

            print(index_fold, middle_fold, ring_fold, "YESS" if sum(r < 1.2 for r in [index_fold, middle_fold, ring_fold]) >=2 else "NOO", "curved grip")
            curved_grip = sum(r < 1.2 for r in [index_fold, middle_fold, ring_fold]) >= 2

            def distance(a, b):
                return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5

            wrist = handLms.landmark[0]
            index_mcp = handLms.landmark[5]
            pinky_mcp = handLms.landmark[17]
            palm_height = distance(wrist, middle_mcp)
            palm_width = distance(index_mcp, pinky_mcp)
            palm_diag = (palm_height ** 2 + palm_width ** 2) ** 0.5
            hand_size = int(palm_diag * w * 0.5)
            hand_size = min(100, max(20, hand_size))  # reasonable size bounds
            print("hand_size", hand_size)
            # Example: launch a ball from the tip of the index finger (id==8)
            current_time = time.time()
            palm_cx = int((wrist.x + middle_mcp.x) / 2 * w)
            palm_cy = int((wrist.y + middle_mcp.y) / 2 * h + 0.05 * h)
            # Always show the ball in hand
            cv2.circle(img, (palm_cx, palm_cy), hand_size, (0, 0, 255), -1)

            # Launch only when hand relaxes (open from curved) and delay passed
            if not curved_grip and current_time - last_launch_time > 5:
                vx, vy = 7, -18
                ball_trajectory.append((palm_cx, palm_cy, vx, vy, current_time, hand_size))
                last_launch_time = current_time

    # Simulate ball flight with bouncing and damping
    new_trajectory = []
    for bx, by, vx, vy, launch_time, size in ball_trajectory:
        t = time.time() - launch_time
        x = int(bx + vx * t)
        y = int(by + vy * t + 0.5 * 9.8 * (t**2))  # simulate gravity
        vy_new = vy + 9.8 * t
        if y >= h - 15 and abs(vy_new) > 5:  # bounce if hitting bottom
            vy_new = -vy_new * 0.6  # lose energy on bounce
            vx *= 0.8  # friction
            launch_time = time.time()
            bx, by = x, h - 15
            new_trajectory.append((bx, by, vx, vy_new, launch_time, size))
        elif 0 <= x < w and 0 <= y < h:
            new_trajectory.append((bx, by, vx, vy, launch_time, size))
            cv2.circle(img, (x, y), size, (0, 0, 255), -1)
    ball_trajectory = new_trajectory

    # Calculate and display FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (139, 0, 0), 3)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
