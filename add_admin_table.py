import sqlite3

try:
    conn = sqlite3.connect('database/jobportal.db')
    cursor = conn.cursor()

    # Create the table
    query = """
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        info TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """
    cursor.execute(query)
    conn.commit()
    print("Table 'admin' created successfully.")

    # Verify
    cursor.execute("PRAGMA table_info(admin)")
    print(cursor.fetchall())
    conn.close()
except Exception as e:
    print(f"Error: {e}")
