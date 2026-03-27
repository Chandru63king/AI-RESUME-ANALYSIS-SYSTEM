import sqlite3
import os

DATABASE = 'database/jobportal.db'

def list_tables():
    if not os.path.exists(DATABASE):
        print(f"Database not found at {DATABASE}")
        return
    
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\nDATABASE TABLES AND RECORD COUNTS:")
    print("-" * 50)
    for table in tables:
        table_name = table['name']
        if table_name == 'sqlite_sequence':
            continue
        try:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"Table: {table_name:<20} | Records: {count}")
        except Exception as e:
            print(f"Table: {table_name:<20} | Error: {e}")
    print("-" * 50)
    db.close()

if __name__ == '__main__':
    list_tables()
