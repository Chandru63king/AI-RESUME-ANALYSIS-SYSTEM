import sqlite3
import os

DATABASE = 'database/jobportal.db'

def update_schema():
    if not os.path.exists(DATABASE):
        print(f"Database not found at {DATABASE}")
        return

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        print("Attempting to add 'phone' column to 'users' table...")
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        conn.commit()
        print("Successfully added 'phone' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("Column 'phone' already exists. Skipping.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    update_schema()
