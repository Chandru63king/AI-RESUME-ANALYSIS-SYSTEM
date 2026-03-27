import sqlite3

def search_db(target):
    conn = sqlite3.connect('database/jobportal.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        table = table_name[0]
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            cols = [description[0] for description in cursor.description]
            for row in rows:
                for val in row:
                    if target.lower() in str(val).lower():
                        print(f"Match for '{target}' in table {table}, row {row}")
        except Exception:
            pass
    conn.close()

if __name__ == "__main__":
    search_db('metric-circle')
    search_db('futhurs')
    search_db('Unique Styles')
    search_db('Start: User uploads')
