import sqlite3
import os

db_path = 'database/jobportal.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT email, password FROM users WHERE role = 'SEEKER' LIMIT 1")
user = cursor.fetchone()
if user:
    print(f"EMAIL: {user[0]}")
    print(f"PASSWORD: {user[1]}")
else:
    print("No seeker found")
conn.close()
