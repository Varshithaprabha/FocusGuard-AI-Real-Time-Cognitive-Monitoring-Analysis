import cv2
import time
import argparse
import os
from dotenv import load_dotenv
from src.detection_engine import DetectionEngine
from src.analyzer import DistractionAnalyzer
from src.feedback_logger import FeedbackLogger

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="AI Study Helper")
    parser.add_argument("--username", type=str, required=True, help="Username of the student")
    args = parser.parse_args()
    
    print(f"Initializing AI Study Helper for user: {args.username}...")
    detector = DetectionEngine()
    analyzer = DistractionAnalyzer()
    logger = FeedbackLogger(username=args.username)

    camera_idx = int(os.getenv("CAMERA_INDEX", 0))
    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Study session started! Press 'q' to quit.")
    
    last_log_time = time.time()
    frame_counter = 0
    cached_signals = {}
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_counter += 1

            # 1. Detect objects & signals (YOLO every 5th frame, MediaPipe every frame in detector)
            if frame_counter % 5 == 0 or not cached_signals:
                signals = detector.detect(frame, run_yolo=True)
                cached_signals['objects'] = signals['objects']
            else:
                signals = detector.detect(frame, run_yolo=False)
                signals['objects'] = cached_signals.get('objects', [])
            
            # 2. Analyze focus
            state = analyzer.analyze(signals)
            stats = analyzer.get_stats()

            # 3. Log data every 5 seconds (to avoid DB spam)
            if time.time() - last_log_time >= 5:
                # Log state to DB using async queue
                logger.log_state(analyzer.session_id, state, stats)
                last_log_time = time.time()

            # 4. Trigger Alerts based on advanced states
            if state == "Distracted":
                logger.notify("🚨 Distraction Detected", "Stay focused! Put your phone away.")
                cv2.putText(frame, "DISTRACTED! Put phone away", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            elif state == "Absent":
                cv2.putText(frame, "User Missing", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            elif state == "Sleeping":
                logger.notify("💤 Sleeping Detected", "Wake up!")
                cv2.putText(frame, "Wake Up!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            elif state == "Yawning":
                cv2.putText(frame, "Yawning... Take a stretch?", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)
            elif state == "Look Away":
                cv2.putText(frame, "Look at the screen!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)
            elif state == "Bad Posture":
                cv2.putText(frame, "Sit up straight!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 3)
            else:
                cv2.putText(frame, "Focusing...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            # Display Stats on Screen
            y_offset = 100
            for key, val in stats.items():
                text = f"{key}: {val}"
                # Using black text with thickness=2 for maximum visibility on a bright background
                cv2.putText(frame, text, (50, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                y_offset += 30

            # 5. Show Frame
            cv2.imshow('AI Study Helper', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        print("Session ended. Saving summary...")
        logger.save_summary(analyzer.get_stats(), analyzer.session_id)
        logger.close()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
