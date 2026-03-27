import sqlite3
import os

DATABASE = 'database/jobportal.db'

def test_candidate_deletion():
    if not os.path.exists(DATABASE):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Ensure we have an application and some history
    app = cursor.execute('SELECT id FROM applications LIMIT 1').fetchone()
    if not app:
        print("No applications to delete.")
        return
    
    app_id = app['id']
    print(f"Targeting App ID {app_id} for deletion test.")
    
    # Add dummy history if none exists
    cursor.execute('INSERT INTO ats_status_history (application_id, old_status, new_status, changed_by) VALUES (?, ?, ?, ?)',
                   (app_id, 'APPLIED', 'TESTING', 1))
    
    conn.commit()
    
    # 2. Simulate server.py deletion logic
    try:
        cursor.execute('DELETE FROM applications WHERE id = ?', (app_id,))
        cursor.execute('DELETE FROM ats_status_history WHERE application_id = ?', (app_id,))
        conn.commit()
        print("SUCCESS: Deletion queries executed.")
        
        # 3. Verify
        check_app = cursor.execute('SELECT id FROM applications WHERE id = ?', (app_id,)).fetchone()
        check_hist = cursor.execute('SELECT id FROM ats_status_history WHERE application_id = ?', (app_id,)).fetchone()
        
        if not check_app and not check_hist:
            print("VERIFIED: Record and history permanently purged.")
        else:
            print("FAILURE: Records still exist after deletion.")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_candidate_deletion()
