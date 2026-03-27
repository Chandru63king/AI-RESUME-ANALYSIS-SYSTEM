import sqlite3
import os

db_path = 'database/jobportal.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Columns to add to applications
    new_cols = [
        ('matched_skills', 'TEXT'),
        ('missing_skills', 'TEXT'),
        ('timeline_data', 'TEXT'),
        ('is_duplicate', 'BOOLEAN DEFAULT 0')
    ]
    
    # Check current columns
    cursor.execute("PRAGMA table_info(applications)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column {col_name} to applications...")
            try:
                cursor.execute(f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists in applications.")
            
    conn.close()
    print("Migration finished.")
else:
    print(f"Database not found at {db_path}")
