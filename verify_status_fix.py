import sqlite3
import os
import json
from datetime import datetime

DATABASE = 'database/jobportal.db'

def test_status_update_final():
    if not os.path.exists(DATABASE):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Pick an application
    app_row = cursor.execute('SELECT id, status FROM applications LIMIT 1').fetchone()
    if not app_row:
        print("No applications found")
        return
    
    app_id = str(app_row['id']) # Simulate string from request.form
    old_status = app_row['status']
    new_status = 'SHORTLISTED'
    
    print(f"Testing status update for App ID {app_id}: {old_status} -> {new_status}")
    
    # Simulate server.py logic
    try:
        # The query we fixed
        application = cursor.execute('''
            SELECT a.*, u.name as seeker_name, u.id as seeker_user_id, j.title as job_title, j.company_id, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            JOIN job_seekers s ON a.seeker_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE a.id = ?
        ''', (int(app_id),)).fetchone()
        
        if not application:
            print("FAILURE: Application not found in join query")
            return
            
        print(f"SUCCESS: Found application via join. Company ID: {application['company_id']}")
        
        # Timeline logic
        timeline = json.loads(application['timeline_data']) if application['timeline_data'] else []
        timeline.append({"status": new_status, "at": datetime.now().strftime("%Y-%m-%d %H:%M")})
        
        cursor.execute('UPDATE applications SET status = ?, timeline_data = ? WHERE id = ?', 
                       (new_status, json.dumps(timeline), int(app_id)))
        
        cursor.execute('''INSERT INTO ats_status_history 
                          (application_id, old_status, new_status, changed_by, notes) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (int(app_id), old_status, new_status, 4, 'Final Verification'))
        
        conn.commit()
        print("SUCCESS: Full status update flow completed.")
        
    except Exception as e:
        print(f"FAILURE: {type(e).__name__}: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_status_update_final()
