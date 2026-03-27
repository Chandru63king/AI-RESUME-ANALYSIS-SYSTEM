import sqlite3
conn = sqlite3.connect('database/jobportal.db')
conn.row_factory = sqlite3.Row
jobs = conn.execute("SELECT id, title, required_skills, min_experience FROM jobs").fetchall()
for job in jobs:
    print(f"ID: {job['id']} | Title: {job['title']} | Skills: {job['required_skills']} | Exp: {job['min_experience']}")
conn.close()
