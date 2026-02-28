import sqlite3

conn = sqlite3.connect("event_finder.db")
cursor = conn.cursor()

# Add category column
cursor.execute("ALTER TABLE saved_events ADD COLUMN category TEXT;")

conn.commit()
conn.close()