import sqlite3

def search_futhurs():
    conn = sqlite3.connect('database/jobportal.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table_name in tables:
        table = table_name[0]
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        for column in columns:
            query = f"SELECT * FROM {table} WHERE \"{column}\" LIKE '%futhurs%';"
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows:
                    print(f"Found match in table {table}, column {column}:")
                    for row in rows:
                        print(row)
            except Exception as e:
                pass

    conn.close()

if __name__ == "__main__":
    search_futhurs()
