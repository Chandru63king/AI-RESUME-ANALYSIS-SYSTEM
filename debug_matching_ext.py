import sqlite3
import json

def dump_db():
    conn = sqlite3.connect('database/jobportal.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- JOBS ---")
    jobs = cursor.execute('SELECT * FROM jobs').fetchall()
    for row in jobs:
        print(dict(row))
        
    print("\n--- JOB SEEKERS ---")
    seekers = cursor.execute('SELECT * FROM job_seekers').fetchall()
    for row in seekers:
        print(dict(row))
        
    print("\n--- RESUMES ---")
    resumes = cursor.execute('SELECT * FROM resumes').fetchall()
    for row in resumes:
        print(dict(row))

    print("\n--- APPLICATIONS ---")
    apps = cursor.execute('SELECT * FROM applications').fetchall()
    for row in apps:
        print(dict(row))
        
    conn.close()

if __name__ == '__main__':
    dump_db()
