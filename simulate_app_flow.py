import sqlite3
import os
import json
from datetime import datetime

DATABASE = 'database/jobportal.db'

def simulate_flow():
    if not os.path.exists(DATABASE):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Pick a seeker (id: 5, user_id: 8)
    seeker = cursor.execute("SELECT * FROM job_seekers WHERE id=5").fetchone()
    print(f"Seeker: {dict(seeker)}")
    
    # 2. Pick a job (id: 51, company_id: 7)
    job = cursor.execute("SELECT * FROM jobs WHERE id=51").fetchone()
    print(f"Job: {dict(job)}")
    
    # 3. Simulate api_apply insertion
    new_app_id = cursor.execute('''
        INSERT INTO applications 
        (job_id, seeker_id, status, applied_at, resume_drive_link, contact_email)
        VALUES (?, ?, 'APPLIED', CURRENT_TIMESTAMP, ?, ?)
    ''', (job['id'], seeker['id'], 'https://drive.google.com/test', 'test@example.com')).lastrowid
    
    print(f"Inserted Application ID: {new_app_id}")
    
    # 4. Check company dashboard query
    company_id = job['company_id']
    apps = cursor.execute('''
        SELECT a.*, u.name as seeker_name, u.email as contact_email, j.title as job_title, a.applied_at
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN job_seekers s ON a.seeker_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE j.company_id = ?
        ORDER BY a.applied_at DESC
    ''', (company_id,)).fetchall()
    
    print(f"Found {len(apps)} apps for company {company_id}")
    found = False
    for a in apps:
        if a['id'] == new_app_id:
            print(f"SUCCESS: New application {new_app_id} is VISIBLE in dashboard query.")
            found = True
            break
    
    if not found:
        print(f"FAILURE: New application {new_app_id} is INVISIBLE!")
        
    conn.rollback() # Don't actually keep the test data
    conn.close()

if __name__ == "__main__":
    simulate_flow()
