
import sqlite3
import datetime

def seed_data():
    conn = sqlite3.connect('database/jobportal.db')
    cursor = conn.cursor()
    
    # Get Users
    seeker = cursor.execute("SELECT id FROM users WHERE email = 'seeker@example.com'").fetchone()
    company = cursor.execute("SELECT id FROM users WHERE role = 'COMPANY' LIMIT 1").fetchone()
    
    if not seeker or not company:
        print("Please run create_users.py first.")
        return

    seeker_id = seeker[0]
    company_id = company[0]
    
    # 1. Seed Notifications
    print("Seeding Notifications...")
    notifications = [
        (seeker_id, 'PROFILE_VIEW', 0, "Google viewed your profile", 0),
        (seeker_id, 'JOB_MATCH', 0, "New match: Senior Developer at Amazon", 0),
        (seeker_id, 'APPLICATION_UPDATE', 0, "Your application to Netflix was viewed", 1)
    ]
    cursor.executemany('INSERT INTO notifications (user_id, type, reference_id, content, is_read) VALUES (?, ?, ?, ?, ?)', notifications)
    
    # 2. Seed Messages
    print("Seeding Messages...")
    # Thread 1: Amazon Recruiter
    cursor.execute('INSERT INTO message_threads (subject, last_message_at) VALUES (?, CURRENT_TIMESTAMP)', ("Role at Amazon",))
    thread_id = cursor.lastrowid
    
    cursor.execute('INSERT INTO message_participants (thread_id, user_id, role) VALUES (?, ?, ?)', (thread_id, seeker_id, 'seeker'))
    cursor.execute('INSERT INTO message_participants (thread_id, user_id, role) VALUES (?, ?, ?)', (thread_id, company_id, 'recruiter'))
    
    messages = [
        (thread_id, company_id, "Hi John, thanks for applying. When can you talk?"),
        (thread_id, seeker_id, "Hi! I am available tomorrow after 2 PM."),
        (thread_id, company_id, "Great, let's schedule a call then.")
    ]
    cursor.executemany('INSERT INTO messages (thread_id, sender_id, content) VALUES (?, ?, ?)', messages)

    conn.commit()
    conn.close()
    print("Data seeded successfully!")

if __name__ == '__main__':
    seed_data()
