import sqlite3
import os

DB_PATH = "data/app.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # Session logs table WITH rating column
    c.execute("""
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            class_level TEXT,
            subject TEXT,
            quiz_score REAL,
            level TEXT,
            learning_style TEXT,
            rating INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 ("admin", "AI_Learn2026!", "admin"))

    # Create default student
    c.execute("SELECT * FROM users WHERE username='khushi'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                 ("khushi", "Study2026!", "student"))

    conn.commit()
    conn.close()