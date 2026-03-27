import sqlite3
import os

db_path = 'database/jobportal.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

try:
    conn = sqlite3.connect(db_path, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='builder_resumes'")
    table = cursor.fetchone()
    if table:
        print("TABLE_EXISTS: builder_resumes")
        cursor.execute("PRAGMA table_info(builder_resumes)")
        cols = cursor.fetchall()
        print(f"COLUMNS: {[c[1] for c in cols]}")
    else:
        print("TABLE_MISSING: builder_resumes")
        
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [t[0] for t in cursor.fetchall()]
    print(f"ALL_TABLES: {all_tables}")
    
    conn.close()
except Exception as e:
    print(f"DB_ERROR: {e}")
