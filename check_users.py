import sqlite3

# Connect to your database
conn = sqlite3.connect("event_finder.db")
cursor = conn.cursor()

# Fetch all users
cursor.execute("SELECT id, username, email, created_at FROM users")
users = cursor.fetchall()

if users:
    for u in users:
        print(f"ID: {u[0]}, Username: {u[1]}, Email: {u[2]}, Created At: {u[3]}")
else:
    print("No users in the database.")

conn.close()