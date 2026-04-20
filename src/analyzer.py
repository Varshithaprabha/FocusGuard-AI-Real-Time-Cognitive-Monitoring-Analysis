import time

class DistractionAnalyzer:
    def __init__(self):
        self.start_time = time.time()
        self.last_update = time.time()
        
        self.total_study_time = 0
        self.total_distraction_time = 0
        self.total_absence_time = 0
        self.total_yawning_time = 0
        self.total_sleeping_time = 0
        self.is_slouching = False
        
        self.current_state = "Starting"
        self.session_id = int(time.time())

    def analyze(self, signals):
        """
        Analyzes detected objects and physiological signals to determine current focus state.
        Signals: 'objects' (list), 'ear' (float), 'mar' (float), 'head_yaw' (float), 'slouching' (bool)
        """
        now = time.time()
        duration = now - self.last_update
        self.last_update = now

        # Use new dict format or fallback to list for tests
        detected_objects = signals.get('objects', []) if isinstance(signals, dict) else signals
        ear = signals.get('ear', 1.0) if isinstance(signals, dict) else 1.0
        mar = signals.get('mar', 0.0) if isinstance(signals, dict) else 0.0
        head_yaw = signals.get('head_yaw', 0.0) if isinstance(signals, dict) else 0.0
        slouching = signals.get('slouching', False) if isinstance(signals, dict) else False

        has_person = 'person' in detected_objects
        has_phone = 'cell phone' in detected_objects
        has_study_material = 'laptop' in detected_objects or 'book' in detected_objects

        self.is_slouching = slouching
        
        if mar <= 0.5:
            self.yawn_start_time = 0

        if has_phone:
            state = "Distracted"
            self.total_distraction_time += duration
        elif not has_person:
            state = "Absent"
            self.total_absence_time += duration
        elif ear < 0.2: # Eyes closed
            state = "Sleeping"
            self.total_distraction_time += duration
            self.total_sleeping_time += duration
            self.yawn_start_time = 0 # Reset yawn
        elif mar > 0.5: # Yawning threshold
            if not getattr(self, 'yawn_start_time', 0):
                self.yawn_start_time = now
            
            if now - self.yawn_start_time > 1.5:
                state = "Yawning"
                self.total_study_time += duration
                self.total_yawning_time += duration
            else:
                state = "Focusing" # Technically they are just starting to open mouth, buffer it
                self.total_study_time += duration
        elif abs(head_yaw) > 0.15: # Looking away significantly
            state = "Look Away"
            self.total_distraction_time += duration
        elif slouching:
            state = "Bad Posture"
            self.total_study_time += duration # Still studying but bad posture
        elif has_study_material:
            state = "Focusing"
            self.total_study_time += duration
        else:
            state = "Idle"
            self.total_study_time += duration

        self.current_state = state
        return state

    def get_stats(self):
        """
        Returns session statistics.
        """
        session_duration = time.time() - self.start_time
        focus_score = self.calculate_focus_score()
        
        # Calculate fatigue score based on yawns and sleeping time
        fatigue_score = min(100, (self.total_yawning_time * 2 + self.total_sleeping_time * 5) / max(session_duration, 1) * 100)
        
        return {
            "session_time": round(session_duration / 60, 2), # in minutes
            "focus_time": round(self.total_study_time / 60, 2),
            "distraction_time": round(self.total_distraction_time / 60, 2),
            "absence_time": round(self.total_absence_time / 60, 2),
            "focus_score": focus_score,
            "status": self.current_state,
            "is_slouching": getattr(self, 'is_slouching', False),
            "fatigue_score": round(fatigue_score, 2)
        }

    def calculate_focus_score(self):
        """
        Focus Score = 100 - (phone_usage_ratio * 50) - (absence_ratio * 30)
        Normalized to 0-100.
        """
        session_duration = time.time() - self.start_time
        if session_duration == 0:
            return 100
            
        penalty_phone = (self.total_distraction_time / session_duration) * 50
        penalty_absence = (self.total_absence_time / session_duration) * 30
        
        score = 100 - penalty_phone - penalty_absence
        return max(0, round(score, 1))
