import sqlite3
import os

DATABASE = 'database/jobportal.db'

def migrate():
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    new_cols = {
        'phone': 'TEXT',
        'education_history': 'TEXT',
        'work_history': 'TEXT'
    }
    
    for col, col_type in new_cols.items():
        try:
            print(f"Adding column {col}...")
            cursor.execute(f"ALTER TABLE job_seekers ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            print(f"Column {col} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
