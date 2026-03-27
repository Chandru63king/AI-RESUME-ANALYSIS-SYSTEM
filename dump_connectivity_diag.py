import sqlite3
import os

DATABASE = 'database/jobportal.db'

def dump_data():
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found.")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- JOBS ---")
    jobs = cursor.execute("SELECT id, company_id, title FROM jobs").fetchall()
    for j in jobs:
        print(dict(j))
        
    print("\n--- COMPANIES ---")
    companies = cursor.execute("SELECT id, user_id, company_name FROM companies").fetchall()
    for c in companies:
        print(dict(c))
        
    print("\n--- APPLICATIONS ---")
    apps = cursor.execute("SELECT id, job_id, seeker_id, applied_at FROM applications").fetchall()
    for a in apps:
        print(dict(a))
        
    conn.close()

if __name__ == "__main__":
    dump_data()
