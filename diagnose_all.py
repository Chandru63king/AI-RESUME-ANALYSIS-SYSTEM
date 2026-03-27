import sqlite3
import os

DATABASE = 'database/jobportal.db'

def diagnose_all_companies():
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found.")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    companies = cursor.execute('SELECT id, company_name, user_id FROM companies').fetchall()
    
    for company in companies:
        print(f"\n--- Checking Company: {company['company_name']} (ID: {company['id']}, UserID: {company['user_id']}) ---")
        
        # 1. Direct count
        direct_count = cursor.execute('''
            SELECT COUNT(*) FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.company_id = ?
        ''', (company['id'],)).fetchone()[0]
        
        # 2. Joined count
        joined_count = cursor.execute('''
            SELECT COUNT(*)
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN job_seekers s ON a.seeker_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE j.company_id = ?
        ''', (company['id'],)).fetchone()[0]
        
        print(f"  Direct apps: {direct_count} | Dashboard apps: {joined_count}")
        
        if direct_count > joined_count:
            print(f"  FAILED: Missing {direct_count - joined_count} apps!")
        else:
            print("  OK")
            
    conn.close()

if __name__ == "__main__":
    diagnose_all_companies()
