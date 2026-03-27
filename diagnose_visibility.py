import sqlite3
import os

DATABASE = 'database/jobportal.db'

def diagnose_visibility(company_user_id):
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found.")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get company info
    company = cursor.execute('SELECT id, company_name FROM companies WHERE user_id = ?', (company_user_id,)).fetchone()
    if not company:
        print(f"No company found for user_id {company_user_id}")
        return
    
    print(f"Diagnosing for Company: {company['company_name']} (ID: {company['id']})")
    
    # 1. Direct count of applications for this company's jobs
    direct_count = cursor.execute('''
        SELECT COUNT(*) FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE j.company_id = ?
    ''', (company['id'],)).fetchone()[0]
    
    print(f"Direct application count (joining jobs only): {direct_count}")
    
    # 2. Joined count (the one used in the dashboard)
    joined_count = cursor.execute('''
        SELECT COUNT(*)
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN job_seekers s ON a.seeker_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE j.company_id = ?
    ''', (company['id'],)).fetchone()[0]
    
    print(f"Dashboard application count (joining jobs, seekers, users): {joined_count}")
    
    if direct_count > joined_count:
        print(f"WARNING: {direct_count - joined_count} applications are INVISIBLE due to join failures!")
        
        # Identify bad applications
        bad_apps = cursor.execute('''
            SELECT a.id, a.job_id, a.seeker_id
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.company_id = ?
            AND a.id NOT IN (
                SELECT a2.id
                FROM applications a2
                JOIN job_seekers s ON a2.seeker_id = s.id
                JOIN users u ON s.user_id = u.id
            )
        ''', (company['id'],)).fetchall()
        
        for app in bad_apps:
            print(f"Invisible App ID: {app['id']} | Job ID: {app['job_id']} | Seeker ID: {app['seeker_id']}")
            # Check why seeker lookup fails
            s_row = cursor.execute('SELECT * FROM job_seekers WHERE id = ?', (app['seeker_id'],)).fetchone()
            if not s_row:
                print(f"  -> REASON: Seeker {app['seeker_id']} does not exist in 'job_seekers' table.")
            else:
                u_row = cursor.execute('SELECT * FROM users WHERE id = ?', (s_row['user_id'],)).fetchone()
                if not u_row:
                    print(f"  -> REASON: User {s_row['user_id']} (linked to seeker) does not exist in 'users' table.")
    else:
        print("SUCCESS: All applications are correctly joined and visible.")
        
    conn.close()

if __name__ == "__main__":
    # Test for company 'timechan' (user_id 16)
    diagnose_visibility(16)
