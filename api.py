from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from typing import Dict, List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from sqlalchemy import create_engine
from src.db import get_sqlalchemy_url, authenticate_user, get_db_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Vite frontend origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(get_sqlalchemy_url())

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(req: LoginRequest):
    user = authenticate_user(req.username, req.password)
    if user:
        return {"success": True, "user_id": user[0], "role": user[1], "username": req.username}
    
    # Auto-register logic or update placeholder password
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password, role FROM users WHERE username = ?", (req.username,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')", (req.username, req.password))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return {"success": True, "user_id": new_id, "role": "user", "username": req.username}
    else:
        user_id, current_pwd, role = row
        if current_pwd == 'password':
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (req.password, user_id))
            conn.commit()
            conn.close()
            return {"success": True, "user_id": user_id, "role": role, "username": req.username}
        else:
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/summary/{user_id}")
def get_summary(user_id: int, role: str):
    try:
        if role == 'developer':
            query = "SELECT s.*, u.username FROM session_summary s JOIN users u ON s.user_id = u.id"
            df = pd.read_sql_query(query, engine)
        else:
            query = f"SELECT * FROM session_summary WHERE user_id = {user_id}"
            df = pd.read_sql_query(query, engine)
        
        # Convert datetime to string for JSON serialization
        if 'start_time' in df.columns:
            df['start_time'] = df['start_time'].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

    async def broadcast_to_user(self, user_id: int, message: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/dashboard/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@app.post("/api/broadcast/{user_id}")
async def broadcast_status(user_id: int):
    await manager.broadcast_to_user(user_id, "UPDATE_AVAILABLE")
    return {"success": True}

@app.get("/api/logs/{user_id}")
def get_logs(user_id: int):
    # Only return logs for their most recent session for the live timeline
    try:
        query_max = f"SELECT MAX(session_id) as sid FROM session_logs WHERE user_id = {user_id}"
        max_df = pd.read_sql_query(query_max, engine)
        if max_df.empty or pd.isna(max_df['sid'].iloc[0]):
            return []
        sid = max_df['sid'].iloc[0]
        
        query = f"SELECT * FROM session_logs WHERE session_id = {sid}"
        df = pd.read_sql_query(query, engine)
        df['timestamp'] = df['timestamp'].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{user_id}")
def get_status(user_id: int):
    """ Used by Chrome Extension to check if user is in focus mode """
    try:
        query = f"SELECT state, timestamp FROM session_logs WHERE user_id = {user_id} ORDER BY timestamp DESC LIMIT 1"
        df = pd.read_sql_query(query, engine)
        if df.empty:
            return {"active": False, "state": "None"}
            
        return {"active": True, "state": df['state'].iloc[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/{user_id}")
def get_analytics(user_id: int):
    """ Advanced analytics for user """
    try:
        query = f"SELECT * FROM session_summary WHERE user_id = {user_id}"
        df = pd.read_sql_query(query, engine)
        
        if df.empty:
            return {"time_of_day": [], "seven_day_avg": None}
            
        # Time of Day Correlation
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['hour'] = df['start_time'].dt.hour
        hourly = df.groupby('hour')['final_score'].mean().reset_index()
        
        time_of_day = [{"hour": int(row['hour']), "score": row['final_score']} for _, row in hourly.iterrows()]
        
        # 7-Day Average Comparison
        now = pd.Timestamp.now()
        df['days_ago'] = (now - df['start_time']).dt.days
        recent_7_days = df[df['days_ago'] <= 7]
        avg_7d = recent_7_days['final_score'].mean() if not recent_7_days.empty else 0
        
        today = df[df['days_ago'] == 0]
        avg_today = today['final_score'].mean() if not today.empty else 0
        
        return {
            "time_of_day": time_of_day,
            "seven_day_avg": avg_7d,
            "today_avg": avg_today
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
