import os
from ultralytics import YOLO

class DetectionEngine:
    def __init__(self, model_name='yolov8n.pt'):
        """
        Initializes the YOLOv8 model.
        Using yolov8n.pt (nano) for real-time performance.
        Exports to ONNX for quantization speedups.
        """
        base_name = os.path.splitext(model_name)[0]
        onnx_model = f"{base_name}.onnx"
        
        if not os.path.exists(onnx_model) and os.path.exists(model_name):
            print(f"Exporting {model_name} to ONNX format for faster inference...")
            model = YOLO(model_name)
            model.export(format="onnx", imgsz=640, dynamic=True)
            
        # Prioritize ONNX for speed, fallback to PT
        if os.path.exists(onnx_model):
            self.model = YOLO(onnx_model, task='detect')
            print(f"Loaded optimized ONNX model: {onnx_model}")
        else:
            self.model = YOLO(model_name)
            print(f"Loaded PyTorch model: {model_name}")
            
        # Standard COCO classes for YOLOv8
        # 0: person, 67: cell phone, 73: laptop, 76: keyboard, 63: laptop, 73: book
        self.target_classes = ['person', 'cell phone', 'laptop', 'book', 'cup', 'bottle']

    def detect(self, frame, run_yolo=True):
        """
        Runs detection on a single frame.
        Returns a dictionary of detected objects and physiological signals.
        """
        import mediapipe as mp
        import math
        
        detected_objects = []
        if run_yolo:
            # YOLO Detection
            results = self.model(frame, verbose=False)
            self.last_results = results # Keep for drawing
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    label = self.model.names[class_id]
                    if label in self.target_classes:
                        detected_objects.append(label)
        
        signals = {
            'objects': list(set(detected_objects)),
            'ear': 1.0,
            'mar': 0.0,
            'head_yaw': 0.0,
            'slouching': False
        }

        # MediaPipe Detection
        try:
            mp_face_mesh = mp.solutions.face_mesh
            mp_pose = mp.solutions.pose
            
            rgb_frame = frame[:, :, ::-1] # BGR to RGB
            
            # Face Mesh (EAR, MAR, Gaze)
            with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5) as face_mesh:
                face_results = face_mesh.process(rgb_frame)
                if face_results.multi_face_landmarks:
                    landmarks = face_results.multi_face_landmarks[0].landmark
                    
                    # Calculate EAR (Eye Aspect Ratio) proxy
                    # Left eye distances (top 159 to bottom 145) / (width 33 to 133)
                    p159 = landmarks[159]
                    p145 = landmarks[145]
                    p33 = landmarks[33]
                    p133 = landmarks[133]
                    left_ear = math.dist((p159.x, p159.y), (p145.x, p145.y)) / max(math.dist((p33.x, p33.y), (p133.x, p133.y)), 0.0001)
                    
                    signals['ear'] = left_ear
                    
                    # Calculate MAR (Mouth Aspect Ratio) proxy
                    p13 = landmarks[13]
                    p14 = landmarks[14]
                    p78 = landmarks[78]
                    p308 = landmarks[308]
                    mar = math.dist((p13.x, p13.y), (p14.x, p14.y)) / max(math.dist((p78.x, p78.y), (p308.x, p308.y)), 0.0001)
                    signals['mar'] = mar
                    
                    # Head Pose Proxy (Yaw) - nose (1) relative to left/right cheeks (234, 454)
                    nose = landmarks[1]
                    left_cheek = landmarks[234]
                    right_cheek = landmarks[454]
                    center_x = (left_cheek.x + right_cheek.x) / 2
                    yaw_diff = nose.x - center_x
                    signals['head_yaw'] = yaw_diff

            # Pose (Slouching)
            with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
                pose_results = pose.process(rgb_frame)
                if pose_results.pose_landmarks:
                    pl = pose_results.pose_landmarks.landmark
                    nose_y =    pl[mp_pose.PoseLandmark.NOSE.value].y
                    shoulder_y = (pl[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y + pl[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2
                    
                    # If shoulders are very close to nose vertically, it implies severe slouching or leaning in too much
                    # This ratio is just a heuristic:
                    vertical_dist = shoulder_y - nose_y
                    if vertical_dist < 0.15: # Configurable threshold
                        signals['slouching'] = True
                        
        except Exception as e:
            pass # Fail gracefully if mediapipe has issues

        return signals

    def draw_detections(self, frame, results):
        """
        Draws bounding boxes on the frame for visualization.
        """
        # We can use ultralytics built-in plot or manual cv2
        return results[0].plot()
