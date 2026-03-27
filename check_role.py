import sqlite3
import os

db_path = 'database/jobportal.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT email, role FROM users WHERE email='seeker@example.com'")
user = cursor.fetchone()
if user:
    print(f"EMAIL: |{user[0]}|")
    print(f"ROLE: |{user[1]}|")
else:
    print("User not found")
conn.close()
