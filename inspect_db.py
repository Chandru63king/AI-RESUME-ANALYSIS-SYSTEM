import sqlite3
import os

db_path = 'database/jobportal.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['companies', 'jobs', 'job_seekers']
    for table in tables:
        print(f"\n--- Columns in {table} ---")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"{col[1]} ({col[2]})")
        except Exception as e:
            print(f"Error checking {table}: {e}")
    
    conn.close()
else:
    print(f"Database not found at {db_path}")
