import sqlite3

conn = sqlite3.connect("event_finder.db")
cursor = conn.cursor()

# Replace with the user ID you want to check
user_id = 3

cursor.execute("""
    SELECT event_name, event_date, event_venue, event_url, saved_at
    FROM saved_events
    WHERE user_id=?
""", (user_id,))

events = cursor.fetchall()

if events:
    for e in events:
        print(f"{e[0]} | {e[1]} | {e[2]} | {e[3]} | Saved at: {e[4]}")
else:
    print("No saved events for this user.")

conn.close()