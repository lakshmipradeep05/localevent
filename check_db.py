import sqlite3

# Connect to the database
conn = sqlite3.connect("event_finder.db")
cursor = conn.cursor()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:", tables)

# Check users table structure
cursor.execute("PRAGMA table_info(users);")
users_info = cursor.fetchall()
print("\nUsers table schema:")
for col in users_info:
    print(col)

# Check saved_events table structure
cursor.execute("PRAGMA table_info(saved_events);")
events_info = cursor.fetchall()
print("\nSaved Events table schema:")
for col in events_info:
    print(col)

conn.close()