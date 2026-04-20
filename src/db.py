import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# Use env var or default
db_url = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'study_planner.db')}")
DB_PATH = db_url.replace("sqlite:///", "")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def get_sqlalchemy_url():
    # Used for pandas.read_sql compatibility with SQLAlchemy
    return db_url

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            user_id INTEGER REFERENCES users(id),
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            state TEXT,
            focus_score REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_summary (
            session_id INTEGER PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_duration REAL,
            focus_time REAL,
            distraction_time REAL,
            absence_time REAL,
            final_score REAL
        )
    ''')
    
    # Gracefully add new columns if they do not exist
    try:
        cursor.execute("ALTER TABLE session_logs ADD COLUMN is_slouching BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE session_logs ADD COLUMN fatigue_score REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE session_summary ADD COLUMN health_score REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass
    
    # Check if empty, run default seeds
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'developer')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('user1', '1234', 'user')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('system', 'none', 'system')")
        
    conn.commit()
    conn.close()

def get_or_create_user(username, role='user'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        user_id = row[0]
    else:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, 'password', role))
        conn.commit()
        user_id = cursor.lastrowid
    conn.close()
    return user_id

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user # returns (id, role) or None
