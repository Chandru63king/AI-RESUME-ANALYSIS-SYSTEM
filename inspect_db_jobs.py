import sqlite3
import os

DATABASE = 'database/jobportal.db'

def inspect_jobs():
    if not os.path.exists(DATABASE):
        print(f"Database not found at {DATABASE}")
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    jobs = cursor.execute('SELECT id, title, required_skills FROM jobs LIMIT 20').fetchall()
    
    print(f"{'ID':<4} | {'Title':<30} | {'Required Skills'}")
    print("-" * 80)
    for job in jobs:
        print(f"{job['id']:<4} | {job['title']:<30} | {job['required_skills']}")

    conn.close()

if __name__ == "__main__":
    inspect_jobs()
