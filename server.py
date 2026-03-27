from flask import Flask, render_template, request, redirect, session, url_for, g, jsonify, Response
import sqlite3
import os
import re
from werkzeug.utils import secure_filename
from ai_engine.resume_parser import ResumeParser
from ai_engine.job_matcher import JobMatchEngine
from functools import wraps
import datetime
import random
import string
import json

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)

# --- Security Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'ADMIN':
            log_event('UNAUTHORIZED_ACCESS', f"Unauthorized attempt to access {request.path}")
            return redirect(url_for('admin_secure_login', error="Access Denied: Administrative privileges required."))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

DATABASE = 'database/jobportal.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('database', exist_ok=True)

# --- AI Engine Init ---

parser = ResumeParser()
matcher = JobMatchEngine()

def init_matcher_cache():
    """Initialize the AI Engine's vector cache."""
    with app.app_context():
        try:
            db = getattr(g, '_database', None)
            if db is None:
                db = sqlite3.connect(DATABASE)
                db.row_factory = sqlite3.Row
            
            jobs = db.execute('SELECT * FROM jobs').fetchall()
            matcher.build_cache(jobs)
            print(f" * AI Engine: Cached {len(jobs)} jobs.")
            
            if getattr(g, '_database', None) is None:
                db.close()
        except Exception as e:
            print(f" * AI Engine Cache Init Failed: {e}")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, '_database'): # Changed from sqlite_db to _database to match get_db
        g._database.close()

# --- Custom Filters for UI ---
def get_time_since(timestamp_str):
    try:
        from datetime import datetime
        # Handle both SQL formats
        try:
            posted = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except:
            posted = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            
        diff = datetime.now() - posted
        seconds = diff.total_seconds()
        
        if seconds < 60: return "Just now"
        if seconds < 3600: return f"{int(seconds // 60)}m ago"
        if seconds < 86400: return f"{int(seconds // 3600)}h ago"
        return f"{int(seconds // 86400)}d ago"
    except:
        return "Recent"

app.jinja_env.filters['timesince'] = get_time_since

def format_currency(value):
    try:
        # Extract number if it has text
        import re
        nums = re.findall(r'\d+', str(value))
        if not nums: return f"₹{value}"
        val = int(nums[0])
        return f"₹{val:,}"
    except:
        return f"₹{value}"

app.jinja_env.filters['currency'] = format_currency

app.jinja_env.filters['currency'] = format_currency

def log_event(event_type, description, user_id=None):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Get client info if in request context
        ip_address = request.remote_addr if request else "System"
        device_info = request.headers.get('User-Agent') if request else "System"
        
        cursor.execute('''INSERT INTO system_logs 
                          (event_type, description, user_id, ip_address, device_info) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (event_type, description, user_id, ip_address, device_info))
        db.commit()

def get_setting(key, default=None):
    with app.app_context():
        db = get_db()
        row = db.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
        return row['value'] if row else default

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Create Tables (Simplified from SQL file for SQLite comp)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            location TEXT,
            description TEXT,
            is_verified BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS job_seekers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            seeker_id TEXT UNIQUE,
            skills TEXT,
            primary_skills TEXT,
            secondary_skills TEXT,
            job_titles TEXT,
            experience_years REAL DEFAULT 0,
            education_level TEXT,
            bio TEXT,
            city TEXT,
            state TEXT,
            profile_photo TEXT,
            resume_scanned BOOLEAN DEFAULT 0,
            auto_send_resume BOOLEAN DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            required_skills TEXT,
            location TEXT,
            salary_range TEXT,
            min_experience REAL DEFAULT 0,
            category TEXT,
            employment_type TEXT,
            work_mode TEXT,
            language TEXT DEFAULT 'English',
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seeker_id INTEGER NOT NULL,
            file_path TEXT,
            skills_extracted TEXT,
            parsed_text TEXT,
            experience_extracted TEXT,
            education_extracted TEXT,
            certifications_extracted TEXT,
            FOREIGN KEY(seeker_id) REFERENCES job_seekers(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            seeker_id INTEGER NOT NULL,
            ai_match_score REAL DEFAULT 0,
            ai_skill_score REAL DEFAULT 0,
            ai_exp_score REAL DEFAULT 0,
            ai_title_score REAL DEFAULT 0,
            matched_skills TEXT,
            missing_skills TEXT,
            status TEXT DEFAULT 'APPLIED',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resume_id INTEGER,
            timeline_data TEXT,
            is_duplicate BOOLEAN DEFAULT 0,
            resume_drive_link TEXT,
            contact_email TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id),
            FOREIGN KEY(seeker_id) REFERENCES job_seekers(id),
            FOREIGN KEY(resume_id) REFERENCES resumes(id)
        )''')
        
        # Performance index for application filtering
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_applications_seeker_job 
                          ON applications(seeker_id, job_id)''')
                          
        cursor.execute('''CREATE TABLE IF NOT EXISTS builder_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_json TEXT, -- Store structured data as JSON
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        db.commit()

def run_migrations():
    """Ensure database schema is up-to-date by adding missing columns and tables."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Create builder_resumes if missing (migration)
        cursor.execute('''CREATE TABLE IF NOT EXISTS builder_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_json TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        
        # --- applications table migrations ---
        cursor.execute("PRAGMA table_info(applications)")
        columns = [row[1] for row in cursor.fetchall()]
        
        needed_cols = [
            ('matched_skills', 'TEXT'),
            ('missing_skills', 'TEXT'),
            ('timeline_data', 'TEXT'),
            ('is_duplicate', 'BOOLEAN DEFAULT 0'),
            ('ai_skill_score', 'REAL DEFAULT 0'),
            ('ai_exp_score', 'REAL DEFAULT 0'),
            ('ai_title_score', 'REAL DEFAULT 0'),
            ('resume_drive_link', 'TEXT'),
            ('contact_email', 'TEXT')
        ]
        
        for col_name, col_type in needed_cols:
            if col_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE applications ADD COLUMN {col_name} {col_type}')
                    print(f" * Database Migration: Added missing column {col_name} to applications table.")
                except Exception as e:
                    print(f" * Database Migration Error on {col_name}: {e}")
        
        db.commit()

        # --- jobs table migrations ---
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        needed_jobs_cols = [
            ('min_experience', 'REAL DEFAULT 0'),
            ('category', 'TEXT'),
            ('employment_type', 'TEXT'),
            ('work_mode', 'TEXT'),
            ('language', "TEXT DEFAULT 'English'")
        ]
        
        for col_name, col_type in needed_jobs_cols:
            if col_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE jobs ADD COLUMN {col_name} {col_type}')
                    print(f" * Database Migration: Added missing column {col_name} to jobs table.")
                except Exception as e:
                    print(f" * Database Migration Error on {col_name} for jobs table: {e}")
        
        db.commit()
        
        # New Tables for Admin Dashboard
        cursor.execute('''CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            description TEXT,
            user_id INTEGER,
            ip_address TEXT,
            device_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            category TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # --- Job Discovery System Patterns ---
        cursor.execute('''CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seeker_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (seeker_id) REFERENCES job_seekers(id)
        )''')

        # --- New Messaging System Tables ---
        cursor.execute('''CREATE TABLE IF NOT EXISTS message_threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS message_participants (
            thread_id INTEGER,
            user_id INTEGER,
            role TEXT,
            last_read_at TIMESTAMP,
            FOREIGN KEY(thread_id) REFERENCES message_threads(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            PRIMARY KEY(thread_id, user_id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER,
            sender_id INTEGER,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(thread_id) REFERENCES message_threads(id),
            FOREIGN KEY(sender_id) REFERENCES users(id)
        )''')

        # --- New ATS Tables ---
        cursor.execute('''CREATE TABLE IF NOT EXISTS ats_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            old_status TEXT,
            new_status TEXT,
            changed_by INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(application_id) REFERENCES applications(id),
            FOREIGN KEY(changed_by) REFERENCES users(id)
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ats_settings (
            company_id INTEGER PRIMARY KEY,
            selection_template TEXT,
            rejection_template TEXT,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )''')

        # --- New Notification Tables ---
        cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            reference_id INTEGER,
            content TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')

        db.commit()
        
        # Initialize default settings if empty
        settings_count = db.execute('SELECT COUNT(*) FROM settings').fetchone()[0]
        if settings_count == 0:
            default_settings = [
                ('min_password_length', '8', 'security'),
                ('failed_login_limit', '5', 'security'),
                ('ai_match_threshold', '70', 'ai'),
                ('maintenance_mode', 'false', 'system')
            ]
            db.executemany('INSERT INTO settings (key, value, category) VALUES (?, ?, ?)', default_settings)
            db.commit()
        
        # Create default admin if not exists
        admin = db.execute('SELECT * FROM users WHERE role = "ADMIN"').fetchone()
        if not admin:
            db.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
                       ('admin63', 'admin@jobportal.ai', 'admin123', 'ADMIN'))
            db.commit()
            print("Default Admin Initialized: admin63 / admin123")

        # Inject Requested "Software Testing" Job if missing
        requested_job = db.execute('SELECT id FROM jobs WHERE title = ? AND location = ?', 
                                  ('Software Testing', 'Tiruppur')).fetchone()
        if not requested_job:
            cursor = db.cursor()
            company = db.execute('SELECT id FROM companies LIMIT 1').fetchone()
            if company:
                db.execute('''INSERT INTO jobs (company_id, title, category, work_mode, language, location, description, required_skills, salary_range)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (company['id'], 'Software Testing', 'Engineering', 'Remote', 'English', 'Tiruppur', 
                            'Testing and quality assurance for enterprise software.', 'Selenium, Python, JIRA', '4 - 8 LPA'))
                db.commit()

def generate_seeker_id():
    """Generate a unique Seeker ID: SKR-YYYY-XXXX"""
    year = datetime.datetime.now().year
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SKR-{year}-{random_str}"

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['email'].strip()
        password = request.form['password'].strip()
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE name = ? OR email = ?', (login_input, login_input)).fetchone()
        
        if user:
            # SHIELDS UP: Prevent Admin login from standard home page
            if user['role'] == 'ADMIN':
                log_event('SECURITY_ALERT', f"Admin {user['name']} attempted login from standard portal")
                return render_template('login.html', error="Unauthorized: Admin access is restricted to the secure portal.")

            if 'status' in user.keys() and user['status'] == 'BLOCKED':
                log_event('LOGIN_BLOCKED', f"Blocked user {user['name']} attempted login", user['id'])
                return render_template('login.html', error="Your account has been blocked.")

            if user['password'] == password:
                db.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
                db.commit()
                log_event('LOGIN_SUCCESS', f"User {user['name']} logged in", user['id'])
                
                session['user_id'] = user['id']
                session['role'] = user['role']
                session['name'] = user['name']
                session['email'] = user['email']
                session.permanent = True
                
                if user['role'] == 'COMPANY': return redirect('/company/dashboard')
                return redirect('/seeker/dashboard')
            else:
                return render_template('login.html', error="Invalid Password")
        else:
            return render_template('login.html', error="Invalid Credentials")
    
    return render_template('login.html')

@app.route('/admin-secure-login', methods=['GET', 'POST'])
@app.route('/admin-secure-login', methods=['GET', 'POST'])
def admin_secure_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE (name = ? OR email = ?) AND role = "ADMIN"', (email, email)).fetchone()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['email'] = user['email']
            session.permanent = True
            log_event('ADMIN_LOGIN', f"Administrator {user['name']} authenticated via secure gate")
            
            # Check for AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {'success': True, 'redirect_url': '/admin/dashboard'}
            
            return redirect('/admin/dashboard')
        else:
            log_event('ADMIN_AUTH_FAILURE', f"Failed admin authentication attempt for {email}")
            
            # Check for AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {'success': False, 'error': "Invalid Credentials"}
                
            return render_template('admin_login.html', error="Invalid Credentials")
            
    return render_template('admin_login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            db.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
            db.commit()
            return render_template('forgot_password.html', message="Password updated successfully! You can now login.")
        else:
            return render_template('forgot_password.html', error="Email not found.")
            
    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form.get('phone', '') # Added phone
        password = request.form['password']
        role = request.form['role']
        
        # Username Verification: Min 6 characters
        if len(username) < 6:
            return render_template('register.html', error="Username must be at least 6 characters.")

        # Password Verification: Min 6 chars, Letters + Numbers
        if len(password) < 6 or not re.search("[a-zA-Z]", password) or not re.search("[0-9]", password):
            return render_template('register.html', error="Password must be at least 6 characters and contain both letters and numbers.")
        
        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store in session for verification
        session['pending_user'] = {
            'username': username,
            'email': email,
            'phone': phone, # Store phone in session
            'password': password,
            'role': role,
            'otp': otp
        }
        
        # SIMULATION: Log OTP to console
        print("\n" + "="*30)
        print(f" OTP FOR {email}: {otp} ")
        print("="*30 + "\n")
        
        return redirect('/verify-otp')
            
    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    pending = session.get('pending_user')
    if not pending:
        return redirect('/register')
        
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == pending['otp']:
            # Success - Create user in database
            db = get_db()
            cursor = db.cursor()
            try:
                # Use separate username and email
                cursor.execute('INSERT INTO users (name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)',
                               (pending['username'], pending['email'], pending.get('phone', ''), pending['password'], pending['role']))
                user_id = cursor.lastrowid
                
                if pending['role'] == 'SEEKER':
                    cursor.execute('INSERT INTO job_seekers (user_id) VALUES (?)', (user_id,))
                elif pending['role'] == 'COMPANY':
                    cursor.execute('INSERT INTO companies (user_id, company_name) VALUES (?, ?)', (user_id, pending['username']))
                    
                db.commit()
                session['user_id'] = user_id
                session['role'] = pending['role']
                session['name'] = pending['username']
                session['email'] = pending['email']
                return render_template('verify_otp.html', email=pending['email'], success=True, otp=pending['otp'])
            except sqlite3.IntegrityError:
                return render_template('verify_otp.html', email=pending['email'], error="User already exists", otp=pending['otp'])
        else:
            return render_template('verify_otp.html', email=pending['email'], error="Invalid OTP. Please try again.", otp=pending['otp'])

    return render_template('verify_otp.html', email=pending['email'], otp=pending['otp'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- Seeker ---
def get_seeker_context():
    if 'user_id' not in session or session['role'] != 'SEEKER': return None
    db = get_db()
    
    seeker_row = db.execute('SELECT * FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if not seeker_row and session.get('role') == 'SEEKER':
        # Self-healing: Create missing seeker profile
        db.execute('INSERT INTO job_seekers (user_id) VALUES (?)', (session['user_id'],))
        db.commit()
        seeker_row = db.execute('SELECT * FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
        log_event('PROFILE_HEALED', f"Automatically created missing seeker profile for user {session.get('name')}", session['user_id'])
    
    seeker = dict(seeker_row) if seeker_row else None
    
    if seeker and not seeker.get('seeker_id'):
        new_sid = generate_seeker_id()
        db.execute('UPDATE job_seekers SET seeker_id = ? WHERE id = ?', (new_sid, seeker['id']))
        db.commit()
        seeker['seeker_id'] = new_sid

    notifications = db.execute('''
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC LIMIT 10
    ''', (session['user_id'],)).fetchall()
    notifications = [dict(n) for n in notifications]
    unread_notifications = sum(1 for n in notifications if not n['is_read'])

    has_db_resume = False
    if seeker:
        res_check = db.execute('SELECT id FROM resumes WHERE seeker_id = ? LIMIT 1', (seeker['id'],)).fetchone()
        has_db_resume = bool(res_check)

    resume_scanned = session.get('resume_scanned', bool(seeker['resume_scanned'] if seeker else False))
    has_resume = session.get('has_resume', has_db_resume)

    analysis_summary = session.get('analysis', {
        "domain": "Pending Analysis", 
        "level": "Pending Analysis", 
        "skills": [],
        "education": "Waiting for Resume",
        "confidence_score": "Pending",
        "market_outlook": "Hidden",
        "ats_score": 0,
        "matched_skills_count": 0
    })

    user = {
        'name': session['name'],
        'photo': seeker['profile_photo'] if seeker and seeker['profile_photo'] else 'static/img/default-avatar.png'
    }

    # Fetch all applications for count/lists
    applications_list = []
    if seeker:
        rows = db.execute('''
            SELECT a.*, j.title as job_title, c.company_name, j.location as job_location, 
                   a.resume_id, a.matched_skills, a.missing_skills, a.timeline_data, a.is_duplicate,
                   j.description as job_desc, j.required_skills as job_skills
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.seeker_id = ?
            ORDER BY a.applied_at DESC
        ''', (seeker['id'],)).fetchall()
        for row in rows:
            app_dict = dict(row)
            app_dict['status'] = app_dict['status'].title() if app_dict['status'] else 'Applied'
            applications_list.append(app_dict)

    recommendations = session.get('recommendations', [])

    return {
        'seeker': seeker,
        'user': user,
        'has_resume': has_resume,
        'resume_scanned': resume_scanned,
        'analysis': analysis_summary,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
        'applications': applications_list,
        'recommendations': recommendations
    }

@app.route('/seeker/dashboard')
@login_required
def seeker_dashboard():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('dashboard_seeker.html', active_page='dashboard', **ctx)

@app.route('/seeker/profile')
@login_required
def seeker_profile():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('seeker_profile.html', active_page='profile', **ctx)

@app.route('/seeker/jobs')
@login_required
def seeker_jobs():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    db = get_db()
    
    # 1. Get Unique Filters for UI
    locations = [row['location'] for row in db.execute('SELECT DISTINCT location FROM jobs ORDER BY location ASC').fetchall() if row['location']]
    categories = [row['category'] for row in db.execute('SELECT DISTINCT category FROM jobs ORDER BY category ASC').fetchall() if row['category']]
    work_modes = [row['work_mode'] for row in db.execute('SELECT DISTINCT work_mode FROM jobs ORDER BY work_mode ASC').fetchall() if row['work_mode']]
    languages = [row['language'] for row in db.execute('SELECT DISTINCT language FROM jobs ORDER BY language ASC').fetchall() if row['language']]
    
    # 2. Get Selected Filters from Query Params
    selected_location = request.args.get('location')
    selected_category = request.args.get('category')
    selected_work_mode = request.args.get('work_mode')
    selected_language = request.args.get('language')
    
    recommendations = ctx['recommendations']
    if recommendations:
        if selected_location and selected_location != 'All':
            recommendations = [j for j in recommendations if j.get('location') == selected_location]
        if selected_category and selected_category != 'All':
            recommendations = [j for j in recommendations if j.get('category') == selected_category]
        if selected_work_mode and selected_work_mode != 'All':
            recommendations = [j for j in recommendations if j.get('work_mode') == selected_work_mode]
        if selected_language and selected_language != 'All':
            recommendations = [j for j in recommendations if j.get('language') == selected_language]
    
    return render_template('seeker_jobs.html', 
                           active_page='jobs', 
                           locations=locations, 
                           categories=categories,
                           work_modes=work_modes,
                           languages=languages,
                           selected_location=selected_location,
                           selected_category=selected_category,
                           selected_work_mode=selected_work_mode,
                           selected_language=selected_language,
                           recommendations=recommendations,
                           **{k: v for k, v in ctx.items() if k != 'recommendations'})

@app.route('/seeker/skills')
@login_required
def seeker_skills():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('seeker_skills.html', active_page='skills', **ctx)

@app.route('/seeker/applied')
@login_required
def seeker_applied():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('seeker_applied.html', active_page='applied', **ctx)

@app.route('/seeker/messages')
@login_required
def seeker_messages_page():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('seeker_messages.html', active_page='messages', **ctx)

@app.route('/seeker/settings')
@login_required
def seeker_settings():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('seeker_settings.html', active_page='settings', **ctx)

@app.route('/seeker/scan')
@login_required
def seeker_scan_page():
    ctx = get_seeker_context()
    if not ctx: return redirect('/login')
    return render_template('seeker_scan.html', active_page='scan', **ctx)

@app.route('/api/jobs/save', methods=['POST'])
@login_required
def api_save_job():
    if session['role'] != 'SEEKER': return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401
    
    job_id = request.form.get('job_id')
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    # Toggle logic
    existing = db.execute('SELECT id FROM saved_jobs WHERE seeker_id = ? AND job_id = ?', 
                          (seeker['id'], job_id)).fetchone()
    
    if existing:
        db.execute('DELETE FROM saved_jobs WHERE id = ?', (existing['id'],))
        action = 'un-saved'
    else:
        db.execute('INSERT INTO saved_jobs (seeker_id, job_id) VALUES (?, ?)', (seeker['id'], job_id))
        action = 'saved'
    
    db.commit()
    return jsonify({'status': 'success', 'action': action})


@app.route('/job/<int:job_id>')
@login_required
def job_detail(job_id):
    db = get_db()
    job = db.execute('''
        SELECT j.*, c.company_name, c.location as company_location, c.description as company_desc, c.is_verified
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.id = ?
    ''', (job_id,)).fetchone()
    
    if not job:
        abort(404)
        
    # Stats for the sidebar
    applied_count = db.execute('SELECT COUNT(*) FROM applications WHERE job_id = ?', (job_id,)).fetchone()[0]
    
    # Check if job is saved (for seekers)
    is_saved = False
    if session.get('role') == 'SEEKER':
        seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
        if seeker:
            saved = db.execute('SELECT 1 FROM saved_jobs WHERE seeker_id = ? AND job_id = ?', 
                               (seeker['id'], job_id)).fetchone()
            is_saved = True if saved else False

    # Simulate social proof (Views)
    import random
    view_count = random.randint(45, 230)

    # Support extended layout by providing full seeker context
    ctx = get_seeker_context()
    if ctx:
        # Merge job-specific data into the seeker context
        ctx.update({
            'job': job,
            'applied_count': applied_count,
            'is_saved': is_saved,
            'view_count': view_count
        })
        return render_template('job_detail.html', **ctx)
    
    # Fallback for non-seekers or if context fails
    user = {'name': session.get('name', 'User')}
    return render_template('job_detail.html', job=job, applied_count=applied_count, is_saved=is_saved, view_count=view_count, user=user)


@app.route('/api/update_profile', methods=['POST'])
@login_required
def api_update_profile():
    if session['role'] != 'SEEKER': return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401
    
    db = get_db()
    name = request.form.get('name')
    job_titles = request.form.get('job_titles')
    city = request.form.get('city')
    state = request.form.get('state')
    bio = request.form.get('bio')
    skills = request.form.get('skills')
    phone = request.form.get('phone')
    education_history = request.form.get('education_history')
    work_history = request.form.get('work_history')
    
    try:
        # Update Users table
        if name:
            db.execute('UPDATE users SET name = ? WHERE id = ?', (name, session['user_id']))
            session['name'] = name # Update session
            
        # Update Job Seekers table
        db.execute('''
            UPDATE job_seekers 
            SET job_titles = ?, city = ?, state = ?, bio = ?, skills = ?, 
                phone = ?, education_history = ?, work_history = ?
            WHERE user_id = ?
        ''', (job_titles, city, state, bio, skills, phone, education_history, work_history, session['user_id']))
        
        db.commit()
        return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/update_profile_photo', methods=['POST'])
@login_required
def api_update_profile_photo():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file:
        filename = secure_filename(f"profile_{session['user_id']}_{file.filename}")
        static_photo_dir = os.path.join('static', 'img')
        filepath = os.path.join(static_photo_dir, filename)
        
        # Ensure directory exists (already should, but safe)
        if not os.path.exists(static_photo_dir):
            os.makedirs(static_photo_dir)
            
        file.save(filepath)
        
        # Update DB - store the /static/... path for easy rendering
        relative_path = f"static/img/{filename}"
        db = get_db()
        db.execute('UPDATE job_seekers SET profile_photo = ? WHERE user_id = ?', (relative_path, session['user_id']))
        db.commit()
        
        return jsonify({'status': 'success', 'photo_url': relative_path})

@app.route('/api/update_seeker_settings', methods=['POST'])
@login_required
def api_update_seeker_settings():
    if session['role'] != 'SEEKER': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    db = get_db()
    
    if 'auto_send_resume' in data:
        db.execute('UPDATE job_seekers SET auto_send_resume = ? WHERE user_id = ?', 
                   (1 if data['auto_send_resume'] else 0, session['user_id']))
        db.commit()
        
        # Notify Seeker
        job_title = db.execute('SELECT title FROM jobs WHERE id = ?', (job_id,)).fetchone()['title']
        add_notification(session['user_id'], 'APPLICATION_SUCCESS', job_id, f"Successfully applied for {job_title}. Good luck!")
        
        return jsonify({'status': 'success'})
        
    return jsonify({'error': 'Invalid request'}), 400

@app.route('/api/apply/<int:job_id>', methods=['POST'])
def api_apply(job_id):
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    
    data = request.json or {}
    drive_link = data.get('drive_link')
    contact_email = data.get('email')
    
    seeker = db.execute('SELECT id, auto_send_resume FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if not seeker and session.get('role') == 'SEEKER':
        # Self-healing in application path
        db.execute('INSERT INTO job_seekers (user_id) VALUES (?)', (session['user_id'],))
        db.commit()
        seeker_row = db.execute('SELECT id, auto_send_resume FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
        log_event('PROFILE_HEALED_AT_APPLY', f"Healed missing profile during application for {session.get('name')}", session['user_id'])
        seeker = dict(seeker_row) if seeker_row else None
    else:
        seeker = dict(seeker) if seeker else None
    
    if not seeker:
        return jsonify({'error': 'Job seeker profile not found'}), 404
        
    # Check if already applied
    existing = db.execute('SELECT id, resume_id FROM applications WHERE job_id = ? AND seeker_id = ?', (job_id, seeker['id'])).fetchone()
    
    match_score, skill_score, exp_score, title_score = 0, 0, 0, 0
    matched_skills, missing_skills = "", ""
    
    # Get match score if resume exists
    resume = db.execute('SELECT id, skills_extracted, parsed_text, experience_extracted FROM resumes WHERE seeker_id = ? ORDER BY id DESC LIMIT 1', (seeker['id'],)).fetchone()
    
    if existing:
        if resume and existing['resume_id'] == resume['id']:
            return jsonify({'error': 'Already applied with this resume version. Update your resume to re-apply.', 'is_duplicate': True}), 400
    
    if resume:
        try:
            job = db.execute('SELECT title, description, required_skills FROM jobs WHERE id = ?', (job_id,)).fetchone()
            if job:
                # Fetch seeker metadata for formal scoring
                seeker_meta = db.execute('SELECT skills, experience_years, education_level FROM job_seekers WHERE id = ?', (seeker['id'],)).fetchone()
                
                # Re-parse or simulate the structured data for scoring
                res_data = {
                    "text": resume['parsed_text'],
                    "primary_skills": resume['skills_extracted'].split(', '), # Fallback grouping
                    "job_titles": [session.get('name', 'Professional')], # Using name as fallback title
                    "experience_years": float(seeker_meta['experience_years'] or 0)
                }
                
                # Use the new formal Scoring Engine
                formal_result = matcher.compute_formal_score(res_data, dict(job))
                match_score = formal_result['match_score']
                skill_score = formal_result['skill_score']
                exp_score = formal_result['exp_score']
                title_score = formal_result['title_score']
                matched_skills = ", ".join(formal_result.get('matched_skills', []))
                missing_skills = ", ".join(formal_result.get('missing_skills', []))
        except Exception as e:
            print(f"Match scoring error: {e}")
            match_score, skill_score, exp_score, title_score = 0, 0, 0, 0
            matched_skills, missing_skills = "", ""
            
    # Auto-link resume if enabled
    res_id = None
    if seeker.get('auto_send_resume', 1) and resume:
        res_id = resume['id']

    import json
    from datetime import datetime
    timeline = json.dumps([{"status": "APPLIED", "at": datetime.now().strftime("%Y-%m-%d %H:%M")}])
    
    is_duplicate = 1 if existing else 0

    db.execute('''INSERT INTO applications 
                  (job_id, seeker_id, ai_match_score, ai_skill_score, ai_exp_score, ai_title_score, 
                   status, applied_at, resume_id, matched_skills, missing_skills, timeline_data, is_duplicate, resume_drive_link, contact_email) 
                  VALUES (?, ?, ?, ?, ?, ?, 'APPLIED', CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)''',
               (job_id, seeker['id'], match_score, skill_score, exp_score, title_score, 
                res_id, matched_skills, missing_skills, timeline, is_duplicate, drive_link, contact_email))
    
    db.commit()
    
    # Remove from session recommendations
    if 'recommendations' in session:
        session['recommendations'] = [
            job for job in session['recommendations'] 
            if job['id'] != job_id
        ]
        session.modified = True
    
    return jsonify({'status': 'success', 'message': 'Application submitted successfully!'})

@app.route('/api/upload_resume', methods=['POST'])
def api_upload_resume():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file:
        file.stream.seek(0) # Ensure Neural Engine v2.0 can read from start
        filename = secure_filename(f"{session['user_id']}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 1. Parse
        data = parser.parse(filepath)
        if "error" in data:
            return jsonify({'error': data['error']}), 400
            
        # Phase 3.1: Mandatory Storage
        db = get_db()
        seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
        if seeker:
            primary_skills_str = ", ".join(data.get('primary_skills', []))
            secondary_skills_str = ", ".join(data.get('secondary_skills', []))
            all_skills_str = ", ".join(list(set(data.get('primary_skills', []) + data.get('secondary_skills', []))))
            job_titles_str = ", ".join(data.get('job_titles', []))
            education_str = data.get('education', 'Not detected')
            
            exp_years = data.get('experience_years', 0)
            exp_label = "Fresher" if exp_years == 0 else f"{exp_years} Years"
            
            # MANDATORY DB INSERT (Requirement)
            db.execute('INSERT INTO resumes (seeker_id, file_path, skills_extracted, parsed_text, experience_extracted, education_extracted) VALUES (?, ?, ?, ?, ?, ?)',
                       (seeker['id'], filepath, all_skills_str, data.get('text', ''), exp_label, education_str))
            
            # Update Job_Seeker_Skills (our job_seekers table)
            db.execute('''
                UPDATE job_seekers 
                SET skills = ?, primary_skills = ?, secondary_skills = ?, job_titles = ?, 
                    experience_years = ?, education_level = ?, resume_scanned = 1
                WHERE id = ?
            ''', (all_skills_str, primary_skills_str, secondary_skills_str, job_titles_str, exp_years, education_str, seeker['id']))
            db.commit()

            # Phase 4.1: Trigger Job Matching 
            all_skills = list(set(data.get('primary_skills', []) + data.get('secondary_skills', [])))
            resume_data = {
            "text": data.get('text', ''),
            "primary_skills": data.get('primary_skills', []),
            "secondary_skills": data.get('secondary_skills', []),
            "job_titles": data.get('job_titles', []),
            "experience_years": data.get('experience_years', 0),
            "education": data.get('education', ''),
            "certifications": data.get('certifications', ''),
            "email": data.get('email', ''),
            "phone": data.get('phone', '')
        }
        
        # Get matches with 40% threshold
        recommendations = matcher.get_top_matches(resume_data, threshold=40, top_n=10)
        
        # Calculate ATS Score using new 50/20/20/10 logic
        ats_score_val = parser.calculate_ats_score(resume_data)
        
        # CRITICAL: Store in session (clears on refresh)
        session['recommendations'] = recommendations
        session['has_resume'] = True
        session['analysis'] = {
            'domain': data.get('primary_domain', 'General'),
            'level': data.get('experience_level', 'Unknown'),
            'skills': all_skills[:10], # Combined for UI section
            'education': data.get('education', 'No education detected'),
            'confidence_score': 'HIGH' if len(all_skills) > 3 else 'MEDIUM',
            'ats_score': ats_score_val,
            'matched_skills_count': len(all_skills)
        }
        session.modified = True
        
        # Generate AI insights for 2026 dashboard
        ats_breakdown = parser.get_ats_breakdown(resume_data)
        seniority = parser.detect_seniority_level(resume_data)
        power_keywords = parser.extract_power_keywords(resume_data, data.get('primary_domain', 'General'))
        
        # Calculate radar scores for visualization
        skills = data.get('skills', [])
        technicalCount = sum(1 for s in skills if any(tk in s.lower() for tk in ['python', 'javascript', 'java', 'react', 'aws', 'sql', 'node']))
        radar_scores = {
            'technical': min(100, (technicalCount / 5) * 100),
            'soft_skills': min(100, (len([k for k in ['leadership', 'communication', 'teamwork', 'problem solving'] if k in data.get('text', '').lower()]) / 3) * 100),
            'experience': min(100, (data.get('experience_years', 0) / 10) * 100),
            'education': 80 if 'bachelor' in data.get('education', '').lower() else 60,
            'market_demand': random.randint(75, 98), # Mock AI Market Demand
            'keywords': ats_breakdown['keywords']
        }
        
        return jsonify({
            'status': 'success',
            'success': True,
            'analysis': session['analysis'],
            'recommendations': recommendations,
            'ats_breakdown': ats_breakdown,
            'seniority': seniority,
            'power_keywords': power_keywords,
            'radar_scores': radar_scores,
            'ai_readiness': {
                'parsed': True,
                'skills_check': True,
                'domain_check': True,
                'job_fit': True
            },
            'market_insights': {
                'outlook': 'High Demand 🚀',
                'skill_demand': f"+{random.randint(5, 20)}% this week",
                'top_regions': 'Global / Remote'
            }
        })
    return jsonify({'error': 'Upload failed'}), 500

@app.route('/api/skill_gap/<int:job_id>', methods=['GET'])
def api_skill_gap(job_id):
    """Get detailed skill gap analysis for a specific job."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if not seeker:
        return jsonify({'error': 'Seeker profile not found'}), 404
    
    # Get latest resume
    resume = db.execute('SELECT skills_extracted, parsed_text, experience_extracted FROM resumes WHERE seeker_id = ? ORDER BY id DESC LIMIT 1', (seeker['id'],)).fetchone()
    
    if not resume:
        return jsonify({'error': 'No resume found. Please upload your resume first.'}), 404
    
    # Get job details
    job = db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Parse experience years
    exp_years = 0
    match = re.search(r'(\d+)', resume['experience_extracted'] or '')
    if match:
        exp_years = float(match.group(1))
    
    resume_data = {
        'text': resume['parsed_text'],
        'skills': resume['skills_extracted'].split(', ') if resume['skills_extracted'] else [],
        'experience_years': exp_years
    }
    
    # Get skill gap analysis
    gap_analysis = matcher.get_skill_gap_analysis(resume_data, dict(job))
    
    return jsonify({
        'status': 'success',
        'job_title': job['title'],
        'company_name': db.execute('SELECT company_name FROM companies WHERE id = ?', (job['company_id'],)).fetchone()['company_name'],
        'gap_analysis': gap_analysis
    })

@app.route('/api/resume_insights', methods=['GET'])
def api_resume_insights():
    """Get comprehensive resume insights including ATS score and quality assessment."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if not seeker:
        return jsonify({'error': 'Seeker profile not found'}), 404
    
    # Get latest resume
    resume = db.execute('SELECT * FROM resumes WHERE seeker_id = ? ORDER BY id DESC LIMIT 1', (seeker['id'],)).fetchone()
    
    if not resume:
        return jsonify({'error': 'No resume found. Please upload your resume first.'}), 404
    
    # Parse experience years
    exp_years = 0
    match = re.search(r'(\d+)', resume['experience_extracted'] or '')
    if match:
        exp_years = float(match.group(1))
    
    resume_data = {
        'text': resume['parsed_text'],
        'skills': resume['skills_extracted'].split(', ') if resume['skills_extracted'] else [],
        'experience_years': exp_years,
        'education': resume['education_extracted'],
        'certifications': resume['certifications_extracted'],
        'email': None,  # Not stored separately
        'phone': None   # Not stored separately
    }
    
    # Get quality assessment
    assessment = parser.get_resume_quality_assessment(resume_data)
    
    return jsonify({
        'status': 'success',
        'assessment': assessment
    })

@app.route('/api/improve_resume', methods=['POST'])
def api_improve_resume():
    """Generate resume improvement suggestions based on current match scores."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if not seeker:
        return jsonify({'error': 'Seeker profile not found'}), 404
    
    # Get latest resume
    resume = db.execute('SELECT * FROM resumes WHERE seeker_id = ? ORDER BY id DESC LIMIT 1', (seeker['id'],)).fetchone()
    
    if not resume:
        return jsonify({'error': 'No resume found. Please upload your resume first.'}), 404
    
    # Parse experience years
    exp_years = 0
    match = re.search(r'(\d+)', resume['experience_extracted'] or '')
    if match:
        exp_years = float(match.group(1))
    
    resume_data = {
        'text': resume['parsed_text'],
        'skills': resume['skills_extracted'].split(', ') if resume['skills_extracted'] else [],
        'experience_years': exp_years,
        'education': resume['education_extracted'],
        'certifications': resume['certifications_extracted']
    }
    
    # Get average match score from session recommendations
    avg_match_score = 0
    missing_skills = []
    
    if 'recommendations' in session and session['recommendations']:
        scores = [job.get('match_score', 0) for job in session['recommendations']]
        avg_match_score = sum(scores) / len(scores) if scores else 0
        
        # Collect all missing skills
        for job in session['recommendations']:
            if 'missing_skills' in job:
                missing_skills.extend(job['missing_skills'])
        
        # Get unique missing skills
        missing_skills = list(set(missing_skills))
    
    # Generate suggestions
    suggestions = parser.generate_improvement_suggestions(resume_data, missing_skills, avg_match_score)
    
    return jsonify({
        'status': 'success',
        'average_match_score': round(avg_match_score, 1),
        'suggestions': suggestions
    })

@app.route('/seeker/upload-resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session: return redirect('/login')
    file = request.files['file']
    if file:
        filename = secure_filename(f"{session['user_id']}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # AI Processing with V2 Error Handling
        data = parser.parse(filepath)
        
        if "error" in data:
            error_msg = f"Resume Parsing Failed: {data['error']}"
            print(error_msg)
            # Fetch base jobs to avoid empty dashboard on error
            db = get_db()
            jobs = db.execute('SELECT * FROM jobs').fetchall()
            return render_template('dashboard_seeker.html', 
                                   user={'name': session['name']}, 
                                   jobs=jobs, 
                                   error=error_msg)

        db = get_db()
        seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
        
        if seeker:
            # skills is now a list from spacy, convert to string
            skills_str = ", ".join(data.get('skills', []))
            
            # Format experience string from years
            exp_years = data.get('experience_years', 0)
            exp_str = f"{exp_years} Years" if exp_years > 0 else "Fresher"
            
            edu_str = data.get('education', 'No education detected')
            certs_str = data.get('certifications', 'None detected')
            
            db.execute('INSERT INTO resumes (seeker_id, file_path, skills_extracted, parsed_text, experience_extracted, education_extracted, certifications_extracted) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (seeker['id'], filepath, skills_str, data.get('text', ''), exp_str, edu_str, certs_str))
            db.execute('UPDATE job_seekers SET skills = ? WHERE id = ?', (skills_str, seeker['id']))
            db.commit()
            
    return redirect('/seeker/dashboard')

@app.route('/seeker/skill-gap')
@login_required
def seeker_skill_gap():
    if session.get('role') != 'SEEKER': return redirect('/login')
    db = get_db()
    
    seeker = db.execute('SELECT * FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    if not seeker: return redirect('/seeker/dashboard')
    
    # Get latest resume for analysis
    resume = db.execute('SELECT * FROM resumes WHERE seeker_id = ? ORDER BY id DESC LIMIT 1', (seeker['id'],)).fetchone()
    
    skills_list = (seeker['skills'] or "").split(', ')
    
    # Categorize skills for Radar Chart
    categories = {
        'Programming': ['python', 'java', 'c++', 'javascript', 'typescript', 'c#', 'ruby', 'go', 'php'],
        'Cloud': ['aws', 'azure', 'gcp', 'cloud', 'architecture', 'serverless', 'lambda'],
        'Architecture': ['microservices', 'design patterns', 'solid', 'architecture', 'system design'],
        'DevOps': ['docker', 'kubernetes', 'jenkins', 'ci/cd', 'terraform', 'ansible', 'monitoring']
    }
    
    radar_data = {cat: 0 for cat in categories}
    for cat, items in categories.items():
        count = sum(1 for s in skills_list if s.lower() in items)
        radar_data[cat] = min(100, count * 25) # Scale to 100
        
    # Get AI Insights - aggregate missing skills from recent recommendations
    missing_skills = []
    avg_score = 0
    if 'recommendations' in session and session['recommendations']:
        scores = [j.get('match_score', 0) for j in session['recommendations']]
        avg_score = sum(scores) / len(scores) if scores else 0
        for j in session['recommendations']:
            missing_skills.extend(j.get('missing_skills', []))
    
    missing_skills = list(set(missing_skills))
    
    res_data = {
        'skills': skills_list,
        'experience_years': float(seeker['experience_years'] or 0),
        'education': seeker['education_level'] or ""
    }
    
    insights = parser.generate_improvement_suggestions(res_data, missing_skills, avg_score)
    
    return render_template('skill_gap.html', 
                           radar_data=radar_data, 
                           known_skills=skills_list,
                           missing_skills=missing_skills[:5], # top 5
                           insights=insights)

@app.route('/seeker/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    if 'user_id' not in session: return redirect('/login')
    db = get_db()
    
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    resume = db.execute('SELECT parsed_text FROM resumes WHERE seeker_id = ? ORDER BY id DESC LIMIT 1', (seeker['id'],)).fetchone()
    job = db.execute('SELECT description, required_skills FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    match_score = 0
    skill_score = 0
    exp_score = 0
    title_score = 0
    if resume and job:
        # Reconstruct seeker metadata for compute_formal_score
        seeker_meta = db.execute('SELECT skills, experience_years FROM job_seekers WHERE id = ?', (seeker['id'],)).fetchone()
        res_data = {
            "text": resume['parsed_text'],
            "primary_skills": (seeker_meta['skills'] or "").split(', '),
            "job_titles": [session.get('name', 'Professional')],
            "experience_years": float(seeker_meta['experience_years'] or 0)
        }
        formal_result = matcher.compute_formal_score(res_data, dict(job))
        match_score = formal_result['match_score']
        skill_score = formal_result['skill_score']
        exp_score = formal_result['exp_score']
        title_score = formal_result['title_score']
    
    db.execute('''INSERT INTO applications 
                  (job_id, seeker_id, ai_match_score, ai_skill_score, ai_exp_score, ai_title_score) 
                  VALUES (?, ?, ?, ?, ?, ?)''',
               (job_id, seeker['id'], match_score, skill_score, exp_score, title_score))
    db.commit()
    return redirect('/seeker/dashboard')


# --- Company ---
@app.route('/company/dashboard')
@login_required
def company_dashboard():
    if session.get('role') != 'COMPANY': return redirect('/login')
    db = get_db()
    
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    if not company: return redirect('/logout')

    # Get Stats
    stats = {
        'total_applicants': db.execute('''SELECT COUNT(*) FROM applications a 
                                        JOIN jobs j ON a.job_id = j.id 
                                        WHERE j.company_id = ?''', (company['id'],)).fetchone()[0],
        'active_jobs': db.execute('SELECT COUNT(*) FROM jobs WHERE company_id = ?', (company['id'],)).fetchone()[0],
        'shortlisted': db.execute('''SELECT COUNT(*) FROM applications a 
                                     JOIN jobs j ON a.job_id = j.id 
                                     WHERE j.company_id = ? AND a.status = "SHORTLISTED"''', (company['id'],)).fetchone()[0]
    }

    applicants = db.execute('''
        SELECT a.*, u.name as seeker_name, u.email as contact_email, j.title as job_title, a.applied_at
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN job_seekers s ON a.seeker_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE j.company_id = ?
        ORDER BY a.applied_at DESC LIMIT 5
    ''', (company['id'],)).fetchall()

    jobs = db.execute('SELECT * FROM jobs WHERE company_id = ? ORDER BY id DESC LIMIT 5', (company['id'],)).fetchall()
    
    return render_template('r-dashboard.html', applicants=applicants, stats=stats, jobs=jobs)

@app.route('/company/postings')
@login_required
def company_postings():
    if session.get('role') != 'COMPANY': return redirect('/login')
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    jobs = db.execute('''
        SELECT j.*, 
        (SELECT COUNT(*) FROM applications WHERE job_id = j.id) as applicant_count,
        (SELECT COUNT(*) FROM applications WHERE job_id = j.id AND status = "SHORTLISTED") as shortlisted_count
        FROM jobs j WHERE company_id = ? ORDER BY posted_at DESC
    ''', (company['id'],)).fetchall()
    
    return render_template('r-postings.html', jobs=jobs)

@app.route('/company/candidates')
@login_required
def company_candidates():
    if session.get('role') != 'COMPANY': return redirect('/login')
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    job_id = request.args.get('job_id')
    query = '''
        SELECT a.*, u.name as seeker_name, u.email as contact_email, j.title as job_title, 
               s.primary_skills, s.secondary_skills, s.experience_years, s.user_id as seeker_user_id,
               a.resume_drive_link, a.applied_at
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN job_seekers s ON a.seeker_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE j.company_id = ?
    '''
    params = [company['id']]
    if job_id:
        query += ' AND a.job_id = ?'
        params.append(job_id)
    
    query += ' ORDER BY a.ai_match_score DESC'
    applicants = db.execute(query, params).fetchall()
    
    return render_template('r-candidates.html', applicants=applicants)

@app.route('/company/messages')
@login_required
def company_messages():
    if session.get('role') != 'COMPANY': return redirect('/login')
    
    seeker_id = request.args.get('seeker_id')
    initial_thread_id = None
    
    if seeker_id:
        db = get_db()
        # Find seeker user_id
        seeker = db.execute('SELECT user_id FROM job_seekers WHERE id = ?', (seeker_id,)).fetchone()
        if seeker:
            initial_thread_id = get_or_create_thread([session['user_id'], seeker['user_id']], subject="Direct Message")
            
    return render_template('r-messages.html', initial_thread_id=initial_thread_id)

@app.route('/company/settings')
@login_required
def company_settings():
    if session.get('role') != 'COMPANY': return redirect('/login')
    return render_template('r-settings.html')

@app.route('/company/post-job', methods=['GET', 'POST'])
@login_required
def company_post_job():
    if session.get('role') != 'COMPANY': return redirect('/login')
    if request.method == 'POST':
        db = get_db()
        company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
        
        db.execute('''INSERT INTO jobs (company_id, title, location, description, required_skills, min_experience, salary_range, category, employment_type, work_mode, language)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (company['id'], request.form['title'], request.form['location'], 
                    request.form['description'], request.form['required_skills'], 
                    request.form['experience'], request.form['salary_range'],
                    request.form.get('category'), request.form.get('employment_type'),
                    request.form.get('work_mode'), request.form.get('language', 'English')))
        db.commit()
        return redirect('/company/postings')
        
    return render_template('r-post-job.html')

@app.route('/company/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def company_edit_job(job_id):
    if session.get('role') != 'COMPANY': return redirect('/login')
    db = get_db()
    
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    job = db.execute('SELECT * FROM jobs WHERE id = ? AND company_id = ?', (job_id, company['id'])).fetchone()
    
    if not job: return redirect('/company/dashboard')

    if request.method == 'POST':
        db.execute('''UPDATE jobs SET 
                      title = ?, location = ?, description = ?, required_skills = ?, 
                      min_experience = ?, salary_range = ?, category = ?, 
                      employment_type = ?, work_mode = ?, language = ?
                      WHERE id = ? AND company_id = ?''',
                   (request.form['title'], request.form['location'], 
                    request.form['description'], request.form['required_skills'], 
                    request.form['experience'], request.form['salary_range'],
                    request.form.get('category'), request.form.get('employment_type'),
                    request.form.get('work_mode'), request.form.get('language', 'English'),
                    job_id, company['id']))
        db.commit()
        return redirect('/company/dashboard')
        
    return render_template('r-edit-job.html', job=job)


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    
    # 1. User Stats
    user_counts = db.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role').fetchall()
    stats = {
        'total_users': sum(c['count'] for c in user_counts),
        'seekers': next((c['count'] for c in user_counts if c['role'] == 'SEEKER'), 0),
        'companies': next((c['count'] for c in user_counts if c['role'] == 'COMPANY'), 0),
        'admins': next((c['count'] for c in user_counts if c['role'] == 'ADMIN'), 0),
        'resumes_total': db.execute('SELECT COUNT(*) FROM resumes').fetchone()[0],
        'jobs_total': db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
        'applications_total': db.execute('SELECT COUNT(*) FROM applications').fetchone()[0]
    }

    # 2. Match Accuracy Data
    matches = db.execute('''SELECT 
        SUM(CASE WHEN ai_match_score >= 70 THEN 1 ELSE 0 END) as high,
        SUM(CASE WHEN ai_match_score >= 40 AND ai_match_score < 70 THEN 1 ELSE 0 END) as med,
        SUM(CASE WHEN ai_match_score < 40 THEN 1 ELSE 0 END) as low
        FROM applications''').fetchone()
    
    match_data = [matches['high'] or 0, matches['med'] or 0, matches['low'] or 0]

    # 3. User Growth (Real query)
    daily_registrations = db.execute('''SELECT strftime('%Y-%m-%d', created_at) as day, count(*) 
                                       FROM users 
                                       GROUP BY day 
                                       ORDER BY day DESC LIMIT 7''').fetchall()
    growth_labels = [row['day'] for row in reversed(daily_registrations)]
    growth_data = [row['count(*)'] for row in reversed(daily_registrations)]

    # 4. User List for Management
    users = db.execute('SELECT id, name, email, role, status, last_login, created_at FROM users ORDER BY created_at DESC').fetchall()
    
    # 5. Latest Logs
    logs = db.execute('''SELECT l.*, u.name as user_name 
                         FROM system_logs l 
                         LEFT JOIN users u ON l.user_id = u.id 
                         ORDER BY l.created_at DESC LIMIT 50''').fetchall()
    
    # 6. Settings
    raw_settings = db.execute('SELECT * FROM settings').fetchall()
    settings = {s['key']: s['value'] for s in raw_settings}

    return render_template('dashboard_admin.html', 
                           stats=stats, 
                           match_data=match_data, 
                           growth_data=growth_data, 
                           growth_labels=growth_labels,
                           users=users, 
                           logs=logs,
                           settings=settings)

@app.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    name = request.form['name']
    email = request.form['email']
    phone = request.form.get('phone', '') # Added phone
    password = request.form['password']
    role = request.form['role']
    
    db = get_db()
    try:
        db.execute('INSERT INTO users (name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)', (name, email, phone, password, role))
        db.commit()
        log_event('USER_ADDED', f"Admin added user {name} ({role})")
    except Exception as e:
        return redirect('/admin/dashboard?error=User already exists')
    return redirect('/admin/dashboard')

@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@admin_required
def admin_edit_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '') # Added phone
        role = request.form['role']
        
        db = get_db()
        db.execute('UPDATE users SET name = ?, email = ?, phone = ?, role = ? WHERE id = ?', (name, email, phone, role, user_id))
        db.commit()
        log_event('USER_EDITED', f"Admin edited user ID {user_id}")
    return redirect('/admin/dashboard')

@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    log_event('USER_DELETED', f"Admin deleted user ID {user_id}")
    return redirect('/admin/dashboard')

@app.route('/admin/users/toggle_status/<int:user_id>')
@admin_required
def admin_toggle_status(user_id):
    db = get_db()
    user = db.execute('SELECT status FROM users WHERE id = ?', (user_id,)).fetchone()
    new_status = 'BLOCKED' if user['status'] == 'ACTIVE' else 'ACTIVE'
    db.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
    db.commit()
    log_event('USER_STATUS_CHANGE', f"Admin changed user ID {user_id} status to {new_status}")
    return redirect('/admin/dashboard')

@app.route('/admin/settings/update', methods=['POST'])
@admin_required
def admin_update_settings():
    db = get_db()
    for key, value in request.form.items():
        db.execute('UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', (value, key))
    db.commit()
    log_event('SETTINGS_UPDATED', "Admin updated system settings")
    return redirect('/admin/dashboard')

@app.route('/admin/logs/clear')
@admin_required
def admin_clear_logs():
    db = get_db()
    db.execute('DELETE FROM system_logs')
    db.commit()
    log_event('LOGS_CLEARED', "Admin cleared system logs")
    return redirect('/admin/dashboard')

# --- Messaging & Notification Utilities ---

def add_notification(user_id, n_type, reference_id, content):
    db = get_db()
    db.execute('INSERT INTO notifications (user_id, type, reference_id, content) VALUES (?, ?, ?, ?)',
               (user_id, n_type, reference_id, content))
    db.commit()

def get_or_create_thread(participant_ids, subject="Direct Message"):
    db = get_db()
    # Simplified thread lookup: find thread where all participant_ids are present
    # In a real app, this would be more complex to match exact participant sets
    placeholders = ','.join(['?'] * len(participant_ids))
    query = f'''
        SELECT thread_id FROM message_participants 
        WHERE user_id IN ({placeholders})
        GROUP BY thread_id 
        HAVING COUNT(DISTINCT user_id) = ?
    '''
    params = list(participant_ids) + [len(participant_ids)]
    row = db.execute(query, params).fetchone()
    
    if row:
        return row['thread_id']
    
    # Create new thread
    cursor = db.cursor()
    cursor.execute('INSERT INTO message_threads (subject) VALUES (?)', (subject,))
    thread_id = cursor.lastrowid
    
    for pid in participant_ids:
        # Determine role from user table
        user = db.execute('SELECT role FROM users WHERE id = ?', (pid,)).fetchone()
        db.execute('INSERT INTO message_participants (thread_id, user_id, role) VALUES (?, ?, ?)',
                   (thread_id, pid, user['role']))
    
    db.commit()
    return thread_id

# --- Messaging Routes ---

@app.route('/api/messages/threads')
@login_required
def get_threads():
    db = get_db()
    threads = db.execute('''
        SELECT t.*, 
               (SELECT content FROM messages WHERE thread_id = t.id ORDER BY created_at DESC LIMIT 1) as last_message,
               (SELECT name FROM users u JOIN message_participants p ON u.id = p.user_id 
                WHERE p.thread_id = t.id AND p.user_id != ? LIMIT 1) as other_party
        FROM message_threads t
        JOIN message_participants p ON t.id = p.thread_id
        WHERE p.user_id = ?
        ORDER BY t.last_message_at DESC
    ''', (session['user_id'], session['user_id'])).fetchall()
    
    return {"threads": [dict(t) for t in threads]}

@app.route('/api/messages/threads/<int:thread_id>')
@login_required
def get_messages(thread_id):
    db = get_db()
    # Check if user is participant
    participant = db.execute('SELECT * FROM message_participants WHERE thread_id = ? AND user_id = ?',
                             (thread_id, session['user_id'])).fetchone()
    if not participant: return {"error": "Access Denied"}, 403
    
    messages = db.execute('''
        SELECT m.*, u.name as sender_name 
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.thread_id = ?
        ORDER BY m.created_at ASC
    ''', (thread_id,)).fetchall()
    
    # Update last_read_at
    db.execute('UPDATE message_participants SET last_read_at = CURRENT_TIMESTAMP WHERE thread_id = ? AND user_id = ?',
               (thread_id, session['user_id']))
    db.commit()
    
    return {"messages": [dict(m) for m in messages]}

@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content')
    thread_id = request.form.get('thread_id')
    
    if not content: return {"error": "Content required"}, 400
    
    db = get_db()
    if not thread_id:
        if not receiver_id: return {"error": "Receiver or Thread ID required"}, 400
        # Check messaging rules
        sender_role = session['role']
        if sender_role == 'COMPANY':
            # Employers can only reply after application or message
            # For simplicity, we'll check if an application exists from the receiver
            seeker_id = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (receiver_id,)).fetchone()
            if seeker_id:
                app_exists = db.execute('SELECT 1 FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.seeker_id = ? AND j.company_id = (SELECT id FROM companies WHERE user_id = ?)',
                                        (seeker_id['id'], session['user_id'])).fetchone()
                if not app_exists: return {"error": "You can only message applicants"}, 403
        
        thread_id = get_or_create_thread([session['user_id'], int(receiver_id)])
    
    cursor = db.cursor()
    cursor.execute('INSERT INTO messages (thread_id, sender_id, content) VALUES (?, ?, ?)',
                   (thread_id, session['user_id'], content))
    msg_id = cursor.lastrowid
    
    db.execute('UPDATE message_threads SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?', (thread_id,))
    db.commit()
    
    # Add notification for participants
    participants = db.execute('SELECT user_id FROM message_participants WHERE thread_id = ? AND user_id != ?',
                              (thread_id, session['user_id'])).fetchall()
    for p in participants:
        add_notification(p['user_id'], 'MESSAGE', msg_id, f"New message from {session['name']}")
    
    return {"success": True, "thread_id": thread_id}

# --- ATS Routes ---

@app.route('/api/ats/update-status', methods=['POST'])
@login_required
def update_ats_status():
    if session['role'] not in ['ADMIN', 'COMPANY']: return {"error": "Unauthorized"}, 403
    
    app_id = request.form.get('application_id')
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    if not app_id or not new_status: return {"error": "Missing data"}, 400
    
    db = get_db()
    # Verify ownership
    application = db.execute('''
        SELECT a.*, u.name as seeker_name, u.id as seeker_user_id, j.title as job_title, j.company_id, c.company_name
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN companies c ON j.company_id = c.id
        JOIN job_seekers s ON a.seeker_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE a.id = ?
    ''', (int(app_id),)).fetchone()
    
    if not application: return {"error": "Application not found"}, 404
    
    if session['role'] == 'COMPANY':
        company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
        if not company or application['company_id'] != company['id']:
            return {"error": "Access Denied"}, 403
    
    old_status = application['status']
    
    # Update timeline
    import json
    from datetime import datetime
    try:
        timeline = json.loads(application['timeline_data']) if application['timeline_data'] else []
    except:
        timeline = []
        
    timeline.append({"status": new_status, "at": datetime.now().strftime("%Y-%m-%d %H:%M")})
    
    db.execute('UPDATE applications SET status = ?, timeline_data = ? WHERE id = ?', 
               (new_status, json.dumps(timeline), app_id))
    db.execute('INSERT INTO ats_status_history (application_id, old_status, new_status, changed_by, notes) VALUES (?, ?, ?, ?, ?)',
               (app_id, old_status, new_status, session['user_id'], notes))
    db.commit()
    
    # Automated Messaging Trigger
    msg_content = ""
    if new_status == 'SHORTLISTED':
        msg_content = f"Congratulations! You've been selected for the position of '{application['job_title']}' at {application['company_name']}. Please wait for further contact."
    elif new_status == 'REJECTED':
        msg_content = f"Thank you for your interest in the position of '{application['job_title']}' at {application['company_name']}. Unfortunately, we have decided to proceed with other candidates."
    
    if msg_content:
        # Send automated message from Company to Seeker
        thread_id = get_or_create_thread([session['user_id'], application['seeker_user_id']], subject=f"Application Update: {application['job_title']}")
        db.execute('INSERT INTO messages (thread_id, sender_id, content) VALUES (?, ?, ?)',
                   (thread_id, session['user_id'], msg_content))
        db.execute('UPDATE message_threads SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?', (thread_id,))
        db.commit()
        
        add_notification(application['seeker_user_id'], 'APPLICATION_STATUS', app_id, f"Application status updated for {application['job_title']}")
    
    return {"success": True}

@app.route('/api/ats/delete-application', methods=['POST'])
@login_required
def delete_ats_application():
    if session['role'] not in ['ADMIN', 'COMPANY']: return {"error": "Unauthorized"}, 403
    
    app_id = request.form.get('application_id')
    if not app_id: return {"error": "Missing application_id"}, 400
    
    db = get_db()
    
    # Ownership Check
    application = db.execute('''
        SELECT a.id, j.company_id
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.id = ?
    ''', (int(app_id),)).fetchone()
    
    if not application: return {"error": "Application not found"}, 404
    
    if session['role'] == 'COMPANY':
        company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
        if not company or application['company_id'] != company['id']:
            return {"error": "Access Denied"}, 403
            
    # Perform Deletion
    db.execute('DELETE FROM applications WHERE id = ?', (int(app_id),))
    db.execute('DELETE FROM ats_status_history WHERE application_id = ?', (int(app_id),))
    db.commit()
    
    log_event('APPLICATION_PURGED', f"Recruiter {session['name']} purged application record {app_id}", session['user_id'])
    
    return {"success": True}

@app.route('/api/jobs/delete', methods=['POST'])
@login_required
def delete_job_vacancy():
    if session['role'] not in ['ADMIN', 'COMPANY']: return {"error": "Unauthorized"}, 403
    
    job_id = request.form.get('job_id')
    if not job_id: return {"error": "Missing job_id"}, 400
    
    db = get_db()
    
    # Ownership Check
    job = db.execute('SELECT company_id FROM jobs WHERE id = ?', (int(job_id),)).fetchone()
    if not job: return {"error": "Job not found"}, 404
    
    if session['role'] == 'COMPANY':
        company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
        if not company or job['company_id'] != company['id']:
            return {"error": "Access Denied"}, 403
            
    # Perform Deletion (Cascade manually since SQLite foreign keys might be OFF)
    # 1. Get associated applications
    apps = db.execute('SELECT id FROM applications WHERE job_id = ?', (int(job_id),)).fetchall()
    app_ids = [row['id'] for row in apps]
    
    if app_ids:
        # Delete history for these apps
        placeholders = ', '.join(['?'] * len(app_ids))
        db.execute(f'DELETE FROM ats_status_history WHERE application_id IN ({placeholders})', app_ids)
        # Delete applications
        db.execute(f'DELETE FROM applications WHERE job_id = ?', (int(job_id),))
    
    # 2. Delete the job itself
    db.execute('DELETE FROM jobs WHERE id = ?', (int(job_id),))
    db.commit()
    
    log_event('JOB_DELETED', f"Recruiter {session['name']} deleted job vacancy {job_id}", session['user_id'])
    
    return {"success": True}


@app.route('/api/applications/export/<format>')
@login_required
def export_applications(format):
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    if not seeker: return jsonify({'error': 'Unauthorized'}), 403
    
    apps = db.execute('''
        SELECT a.*, j.title, c.company_name, a.ai_match_score, a.status, a.applied_at
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN companies c ON j.company_id = c.id
        WHERE a.seeker_id = ?
    ''', (seeker['id'],)).fetchall()
    
    if format == 'csv':
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Company', 'Job Title', 'Applied At', 'Score', 'Status'])
        for a in apps:
            writer.writerow([a['company_name'], a['title'], a['applied_at'], a['ai_match_score'], a['status']])
        
        output.seek(0)
        return Response(output.read(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=applications.csv"})
    
@app.route('/api/applications/withdraw/<int:app_id>', methods=['POST'])
@login_required
def withdraw_application(app_id):
    if session['role'] != 'SEEKER': return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    if not seeker: return jsonify({'error': 'Seeker not found'}), 404
    
    # Verify ownership
    application = db.execute('SELECT * FROM applications WHERE id = ? AND seeker_id = ?', (app_id, seeker['id'])).fetchone()
    if not application: return jsonify({'error': 'Application not found or unauthorized'}), 404
    
    if application['status'] == 'WITHDRAWN':
        return jsonify({'error': 'Application is already withdrawn'}), 400
        
    # Update status and timeline
    import json
    from datetime import datetime
    try:
        timeline = json.loads(application['timeline_data']) if application['timeline_data'] else []
    except:
        timeline = []
        
    timeline.append({"status": "WITHDRAWN", "at": datetime.now().strftime("%Y-%m-%d %H:%M")})
    
    db.execute('UPDATE applications SET status = "WITHDRAWN", timeline_data = ? WHERE id = ?', 
               (json.dumps(timeline), app_id))
    db.commit()
    
    return jsonify({'success': True, 'message': 'Application withdrawn successfully'})

@app.route('/api/applications/delete/<int:app_id>', methods=['POST'])
@login_required
def delete_seeker_application(app_id):
    if session['role'] != 'SEEKER': return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    seeker = db.execute('SELECT id FROM job_seekers WHERE user_id = ?', (session['user_id'],)).fetchone()
    if not seeker: return jsonify({'error': 'Seeker not found'}), 404
    
    # Verify ownership
    application = db.execute('SELECT * FROM applications WHERE id = ? AND seeker_id = ?', (app_id, seeker['id'])).fetchone()
    if not application: return jsonify({'error': 'Application not found or unauthorized'}), 404
    
    # Perform Deletion
    db.execute('DELETE FROM applications WHERE id = ?', (app_id,))
    db.execute('DELETE FROM ats_status_history WHERE application_id = ?', (app_id,))
    db.commit()
    
    log_event('APPLICATION_DELETED_BY_SEEKER', f"Seeker {session['name']} deleted application record {app_id}", session['user_id'])
    
    return jsonify({'success': True, 'message': 'Application record deleted successfully'})

# --- Search API (Existing) ---
@app.route('/api/search_jobs')
def api_search_jobs():
    query = request.args.get('q', '').lower()
    location = request.args.get('location', '').lower()
    
    db = get_db()
    sql = 'SELECT j.*, c.company_name, c.profile_photo as company_logo FROM jobs j JOIN companies c ON j.company_id = c.id WHERE 1=1'
    params = []
    
    if query:
        sql += ' AND (lower(j.title) LIKE ? OR lower(j.description) LIKE ? OR lower(j.required_skills) LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%', f'%{query}%'])
        
    if location and location != 'all':
        sql += ' AND lower(j.location) LIKE ?'
        params.append(f'%{location}%')
        
    jobs = db.execute(sql, params).fetchall()
    
    return jsonify({
        'count': len(jobs),
        'results': [dict(job) for job in jobs]
    })

# --- All Vacancies API (New) ---
@app.route('/api/all_jobs')
@login_required
def api_all_jobs():
    db = get_db()
    jobs = db.execute('''
        SELECT j.*, c.company_name, c.profile_photo as company_logo 
        FROM jobs j 
        JOIN companies c ON j.company_id = c.id
        ORDER BY j.posted_at DESC
    ''').fetchall()
    
    return jsonify({
        'count': len(jobs),
        'results': [dict(job) for job in jobs]
    })

# --- Notification API (New) ---
@app.route('/api/notifications')
@login_required
def api_notifications():
    db = get_db()
    notifs = db.execute('''
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (session['user_id'],)).fetchall()
    
    return jsonify({
        'notifications': [dict(n) for n in notifs],
        'unread_count': sum(1 for n in notifs if not n['is_read'])
    })

@app.route('/api/notifications/mark_read', methods=['POST'])
@login_required
def api_notifications_mark_read():
    db = get_db()
    db.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (session['user_id'],))
    db.commit()
    return jsonify({'status': 'success'})

# --- Messaging API (New) ---
@app.route('/api/messages/threads')
@login_required
def api_message_threads():
    db = get_db()
    user_id = session['user_id']
    
    # 1. Find threads where current user is a participant
    threads = db.execute('''
        SELECT t.id, t.last_message_at,
               (SELECT content FROM messages WHERE thread_id = t.id ORDER BY created_at DESC LIMIT 1) as last_message
        FROM message_threads t
        JOIN message_participants p ON t.id = p.thread_id
        WHERE p.user_id = ?
        ORDER BY t.last_message_at DESC
    ''', (user_id,)).fetchall()
    
    results = []
    for t in threads:
        # 2. Find the "other" participant name
        other = db.execute('''
            SELECT u.name, u.role, u.id
            FROM message_participants p
            JOIN users u ON p.user_id = u.id
            WHERE p.thread_id = ? AND p.user_id != ?
        ''', (t['id'], user_id)).fetchone()
        
        results.append({
            'id': t['id'],
            'other_party': other['name'] if other else 'Unknown',
            'other_party_id': other['id'] if other else None,
            'last_message': t['last_message'] or 'No messages yet',
            'last_message_time': t['last_message_at']
        })
        
    return jsonify({'threads': results})

@app.route('/api/messages/threads/<int:thread_id>')
@login_required
def api_message_thread_detail(thread_id):
    db = get_db()
    user_id = session['user_id']
    
    # Verify participation
    part = db.execute('SELECT * FROM message_participants WHERE thread_id = ? AND user_id = ?', (thread_id, user_id)).fetchone()
    if not part:
        return jsonify({'error': 'Unauthorized'}), 401
        
    messages = db.execute('''
        SELECT m.*, u.name as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.thread_id = ?
        ORDER BY m.created_at ASC
    ''', (thread_id,)).fetchall()
    
    return jsonify({
        'messages': [dict(m) for m in messages]
    })

@app.route('/api/messages/send', methods=['POST'])
@login_required
def api_message_send():
    thread_id = request.form.get('thread_id')
    content = request.json.get('content') if request.is_json else request.form.get('content') # Support both
    
    if not thread_id or not content:
        return jsonify({'error': 'Missing data'}), 400
        
    db = get_db()
    user_id = session['user_id']
    
    # Verify participation
    part = db.execute('SELECT * FROM message_participants WHERE thread_id = ? AND user_id = ?', (thread_id, user_id)).fetchone()
    if not part:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Insert Message
    db.execute('INSERT INTO messages (thread_id, sender_id, content) VALUES (?, ?, ?)', (thread_id, user_id, content))
    
    # Notify OTHER participant
    other = db.execute('SELECT user_id FROM message_participants WHERE thread_id = ? AND user_id != ?', 
                      (thread_id, user_id)).fetchone()
    if other:
        sender_name = session.get('name', 'Someone')
        add_notification(other['user_id'], 'NEW_MESSAGE', thread_id, f"New message from {sender_name}")

    # Update Thread timestamp
    db.execute('UPDATE message_threads SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?', (thread_id,))
    db.commit()
    
    return jsonify({'status': 'success'})


# --- Profile Update ---

if __name__ == '__main__':
    # Initialize DB and Cache on startup
    with app.app_context():
        # Ensure DB tables exist
        if not os.path.exists(DATABASE):
            init_db()
        else:
            # Check if tables exist, if not init
            db = get_db()
            try:
                db.execute('SELECT 1 FROM users LIMIT 1')
            except sqlite3.OperationalError:
                init_db()
        
        # Always run migrations to ensure schema is correct
        run_migrations()
                
        # Cache jobs for AI Engine
        try:
            init_matcher_cache()
        except Exception as e:
            print(f"Cache init failed: {e}")

    app.run(debug=False, port=5000)
