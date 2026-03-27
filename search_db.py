import sqlite3

def search_db(search_str):
    conn = sqlite3.connect('database/jobportal.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        for row in rows:
            if any(search_str.lower() in str(col).lower() for col in row):
                print(f"Found in table '{table}': {row}")
                
    conn.close()

if __name__ == '__main__':
    search_db('chanking')
    print("Search for 'metric-circle':")
    search_db('metric-circle')
