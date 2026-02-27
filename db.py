# db.py
import sqlite3

# Connect to database (it will create it if not exists)
conn = sqlite3.connect("event_finder.db", check_same_thread=False)
cursor = conn.cursor()

# Create Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Create Saved Events Table (optional)
cursor.execute("""
CREATE TABLE IF NOT EXISTS saved_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    event_name TEXT,
    event_date TEXT,
    event_venue TEXT,
    event_url TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

conn.commit()
conn.close()