import sqlite3
import json

def dump_db():
    conn = sqlite3.connect('database/jobportal.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- USERS ---")
    users = cursor.execute('SELECT * FROM users').fetchall()
    for row in users:
        print(dict(row))
        
    print("\n--- JOB SEEKERS ---")
    seekers = cursor.execute('SELECT * FROM job_seekers').fetchall()
    for row in seekers:
        print(dict(row))
        
    conn.close()

if __name__ == '__main__':
    dump_db()
