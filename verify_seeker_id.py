import sqlite3
import os
import datetime
import random
import string

DATABASE = 'database/jobportal.db'

def generate_seeker_id():
    year = datetime.datetime.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SKR-{year}-{random_str}"

def verify():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get a seeker
    cursor.execute('SELECT id, user_id, seeker_id FROM job_seekers LIMIT 1')
    seeker = cursor.fetchone()
    
    if seeker:
        sid, uid, cur_sid = seeker
        print(f"Checking Seeker ID for Seeker {sid} (User {uid}). Current ID: {cur_sid}")
        
        if not cur_sid:
            new_sid = generate_seeker_id()
            print(f"Generating new ID: {new_sid}")
            cursor.execute('UPDATE job_seekers SET seeker_id = ? WHERE id = ?', (new_sid, sid))
            conn.commit()
            print("ID updated successfully.")
        else:
            print("Seeker already has an ID.")
            
    cursor.execute('SELECT user_id, seeker_id FROM job_seekers')
    print("Database State:", cursor.fetchall())
    conn.close()

if __name__ == "__main__":
    verify()
