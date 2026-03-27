import sqlite3

def create_users():
    conn = sqlite3.connect('database/jobportal.db')
    cursor = conn.cursor()

    users = [
        ('Admin User', 'admin@example.com', 'admin123', 'ADMIN'),
        ('Tech Corp', 'company@example.com', 'company123', 'COMPANY'),
        ('John Doe', 'seeker@example.com', 'seeker123', 'SEEKER')
    ]

    print("Creating users...")
    for name, email, password, role in users:
        try:
            # Check if exists
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                print(f"User {email} already exists.")
                continue

            # Insert User
            cursor.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                           (name, email, password, role))
            user_id = cursor.lastrowid
            print(f"Created {role} user: {email}")

            # Insert Role specific data
            if role == 'SEEKER':
                cursor.execute('INSERT INTO job_seekers (user_id) VALUES (?)', (user_id,))
            elif role == 'COMPANY':
                cursor.execute('INSERT INTO companies (user_id, company_name) VALUES (?, ?)', (user_id, name))

        except Exception as e:
            print(f"Error creating {email}: {e}")

    conn.commit()
    conn.close()
    print("Done!")

if __name__ == '__main__':
    create_users()
