import sqlite3

# Connect to the database
conn = sqlite3.connect("event_finder.db")
cursor = conn.cursor()

# ----------------------------
# 1. Insert a test user
# ----------------------------
try:
    cursor.execute("""
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
    """, ("testuser", "test@example.com", "password123"))
    conn.commit()
    print("Test user inserted successfully!")
except sqlite3.IntegrityError:
    print("Test user already exists.")

# Get the user ID
cursor.execute("SELECT id FROM users WHERE username=?", ("testuser",))
user_id = cursor.fetchone()[0]

# ----------------------------
# 2. Insert a test saved event
# ----------------------------
cursor.execute("""
    INSERT INTO saved_events (user_id, event_name, event_date, event_venue, event_url)
    VALUES (?, ?, ?, ?, ?)
""", (user_id, "Test Concert", "2026-03-05", "Test Arena", "http://example.com"))
conn.commit()
print("Test event inserted successfully!")

# ----------------------------
# 3. Query back saved events
# ----------------------------
cursor.execute("SELECT event_name, event_date, event_venue, event_url FROM saved_events WHERE user_id=?", (user_id,))
saved_events = cursor.fetchall()

print("\nSaved Events for testuser:")
for event in saved_events:
    print(f"• {event[0]} on {event[1]} at {event[2]} ({event[3]})")

conn.close()