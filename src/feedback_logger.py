import os
import time
import threading
import queue
import asyncio
import websockets
from win10toast import ToastNotifier
from src.db import get_db_connection, init_db, get_or_create_user

class FeedbackLogger:
    def __init__(self, username="system"):
        self.toaster = ToastNotifier()
        self.last_alert_time = 0
        self.alert_cooldown = 30 # seconds
        self.username = username
        
        # Initialize tables and get user ID
        try:
            init_db()
            self.user_id = get_or_create_user(username)
        except Exception as e:
            print(f"Database error ({e}).")
            self.user_id = 1

        self.log_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _worker(self):
        """Background thread to process db writes and api broadcasts sequentially."""
        while True:
            task = self.log_queue.get()
            if task is None:
                break
            
            action, data = task
            if action == 'log_state':
                session_id, user_id, state, focus_score, is_slouching, fatigue_score = data
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO session_logs (session_id, user_id, state, focus_score, is_slouching, fatigue_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (session_id, user_id, state, focus_score, is_slouching, fatigue_score))
                    # Also broadcast to Fast API WebSocket endpoint securely
                    try:
                        async def send_ws():
                            ws_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws/dashboard/") + str(user_id)
                            async with websockets.connect(ws_url) as ws:
                                await ws.send("UPDATE_AVAILABLE")
                        asyncio.run(send_ws())
                    except:
                        pass
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Async log failed: {e}")
                    
            elif action == 'save_summary':
                session_id, user_id, stats = data
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Assuming health score is calculated or derived later, default to fatigue diff or logic
                    health_score = 100 - stats.get('fatigue_score', 0)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO session_summary 
                        (session_id, user_id, total_duration, focus_time, distraction_time, absence_time, final_score, health_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (session_id, user_id, stats['session_time'], stats['focus_time'], 
                          stats['distraction_time'], stats['absence_time'], stats['focus_score'], health_score))
                    try:
                        async def send_ws():
                            ws_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws/dashboard/") + str(user_id)
                            async with websockets.connect(ws_url) as ws:
                                await ws.send("UPDATE_AVAILABLE")
                        asyncio.run(send_ws())
                    except:
                        pass
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Failed to save summary: {e}")
                    
            self.log_queue.task_done()

    def log_state(self, session_id, state, stats):
        # Push to queue instead of blocking (pass stats to extract focus_score, is_slouching, fatigue_score)
        self.log_queue.put(('log_state', (session_id, self.user_id, state, stats['focus_score'], stats.get('is_slouching', False), stats.get('fatigue_score', 0.0))))

    def notify(self, title, message):
        import time
        if time.time() - self.last_alert_time > self.alert_cooldown:
            # self.toaster.show_toast(title, message, duration=5, threaded=True)
            print(f"NOTIFICATION: {title} - {message}") 
            self.last_alert_time = time.time()

    def save_summary(self, stats, session_id):
        self.log_queue.put(('save_summary', (session_id, self.user_id, stats)))

    def close(self):
        self.log_queue.put(None)
        self.worker_thread.join(timeout=3)
