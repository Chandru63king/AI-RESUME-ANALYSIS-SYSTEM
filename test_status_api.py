import sqlite3
import os

DATABASE = 'database/jobportal.db'

def test_status_update():
    if not os.path.exists(DATABASE):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Pick an application (e.g., ID 1 or any existing one)
    app = cursor.execute('SELECT id, status FROM applications LIMIT 1').fetchone()
    if not app:
        print("No applications found to test")
        return
    
    app_id = app['id']
    old_status = app['status']
    new_status = 'SHORTLISTED' if old_status != 'SHORTLISTED' else 'REJECTED'
    
    print(f"Testing status update for App ID {app_id}: {old_status} -> {new_status}")
    
    # Try to simulate the logic in server.py
    try:
        # Update app status
        cursor.execute('UPDATE applications SET status = ? WHERE id = ?', (new_status, app_id))
        
        # Insert into history (This is where I suspect it might fail if table missing, but I checked run_migrations)
        cursor.execute('''INSERT INTO ats_status_history 
                          (application_id, old_status, new_status, changed_by, notes) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (app_id, old_status, new_status, 4, 'Diagnostic Test')) # Assuming user 4 is a recruiter
        
        conn.commit()
        print("SUCCESS: Database update and history insertion worked.")
        
        # Verify
        updated = cursor.execute('SELECT status FROM applications WHERE id = ?', (app_id,)).fetchone()
        print(f"Verified Status: {updated['status']}")
        
    except sqlite3.OperationalError as e:
        print(f"FAILURE: SQLite Error: {e}")
    except Exception as e:
        print(f"FAILURE: General Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_status_update()
