import sqlite3
import os

db_path = 'database/jobportal.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current columns in applications
    cursor.execute("PRAGMA table_info(applications)")
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'resume_id' not in cols:
        print("Adding column resume_id to applications...")
        try:
            cursor.execute("ALTER TABLE applications ADD COLUMN resume_id INTEGER REFERENCES resumes(id)")
            conn.commit()
        except Exception as e:
            print(f"Error adding resume_id: {e}")
    else:
        print("Column resume_id already exists in applications.")
        
    # Also ensure job_seekers has auto_send_resume preference
    cursor.execute("PRAGMA table_info(job_seekers)")
    seeker_cols = [col[1] for col in cursor.fetchall()]
    if 'auto_send_resume' not in seeker_cols:
        print("Adding column auto_send_resume to job_seekers...")
        try:
            cursor.execute("ALTER TABLE job_seekers ADD COLUMN auto_send_resume BOOLEAN DEFAULT 1")
            conn.commit()
        except Exception as e:
            print(f"Error adding auto_send_resume: {e}")
    else:
        print("Column auto_send_resume already exists in job_seekers.")

    conn.close()
    print("Migration finished.")
else:
    print(f"Database not found at {db_path}")
