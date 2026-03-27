import sqlite3
import os

db_path = 'database/jobportal.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute("PRAGMA table_info(companies)")
    cols = [col[1] for col in cursor.fetchall()]
    
    # Columns to add
    new_cols = [
        ('location', 'TEXT'),
        ('description', 'TEXT'),
        ('is_verified', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_type in new_cols:
        if col_name not in cols:
            print(f"Adding column {col_name} to companies...")
            try:
                cursor.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists in companies.")
            
    conn.close()
    print("Migration finished.")
else:
    print(f"Database not found at {db_path}")
