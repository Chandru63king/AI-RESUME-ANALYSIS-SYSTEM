import sqlite3
import os

DATABASE = 'database/jobportal.db'

def migrate():
    if not os.path.exists(DATABASE):
        print("Database not found. Skipping migration.")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Check for missing columns in job_seekers
    cursor.execute("PRAGMA table_info(job_seekers)")
    columns = [col[1] for col in cursor.fetchall()]

    new_cols = {
        'seeker_id': 'TEXT',
        'bio': 'TEXT',
        'city': 'TEXT',
        'state': 'TEXT'
    }

    for col, type_ in new_cols.items():
        if col not in columns:
            print(f"Adding column {col} to job_seekers...")
            try:
                cursor.execute(f"ALTER TABLE job_seekers ADD COLUMN {col} {type_}")
            except Exception as e:
                print(f"Error adding {col}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
