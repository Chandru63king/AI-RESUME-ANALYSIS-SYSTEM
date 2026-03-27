import sqlite3
import json

DATABASE = 'database/jobportal.db'

# Data provided by user
jobs_data = {
  "job_vacancies": [
    {"id": 1, "title": "Software Developer", "company": "IT Company", "skills": ["Python", "Java", "Cloud", "Agile", "DevOps"], "location": "Coimbatore"},
    {"id": 2, "title": "Frontend Engineer", "company": "Software Company", "skills": ["React", "Angular", "JavaScript", "HTML", "CSS"], "location": "Bangalore"},
    {"id": 3, "title": "Data Scientist", "company": "IT Company", "skills": ["Machine Learning", "SQL", "R", "Python", "Data Visualization"], "location": "Chennai"},
    {"id": 4, "title": "Cybersecurity Analyst", "company": "IT Company", "skills": ["Network Security", "Ethical Hacking", "Firewall", "Cryptography"], "location": "Mumbai"},
    {"id": 5, "title": "Bank Manager", "company": "Bank", "skills": ["Finance", "Leadership", "Customer Service", "Operations", "Compliance"], "location": "Coimbatore"},
    {"id": 6, "title": "Credit Analyst", "company": "Bank", "skills": ["Financial Modeling", "Risk Assessment", "Credit Analysis", "Accounting"], "location": "Bangalore"},
    {"id": 7, "title": "Full Stack Developer", "company": "Software Company", "skills": ["Node.js", "MongoDB", "React", "Express", "Full Stack Development"], "location": "Chennai"},
    {"id": 8, "title": "DevOps Engineer", "company": "IT Company", "skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Automation"], "location": "Mumbai"},
    {"id": 9, "title": "Mobile App Developer", "company": "Software Company", "skills": ["iOS", "Android", "Swift", "Kotlin", "Mobile UI/UX"], "location": "Coimbatore"},
    {"id": 10, "title": "Database Administrator", "company": "IT Company", "skills": ["SQL", "Oracle", "MongoDB", "Database Management", "Backup"], "location": "Bangalore"},
    {"id": 11, "title": "Business Analyst", "company": "Bank", "skills": ["Data Analysis", "Project Management", "Stakeholder Communication", "Process Improvement"], "location": "Chennai"},
    {"id": 12, "title": "QA Engineer", "company": "Software Company", "skills": ["Manual Testing", "Automation Testing", "Selenium", "QA Methodology", "Agile"], "location": "Mumbai"},
    {"id": 13, "title": "Network Engineer", "company": "IT Company", "skills": ["Cisco", "Juniper", "Cloud Networking", "TCP/IP", "Network Troubleshooting"], "location": "Coimbatore"},
    {"id": 14, "title": "Product Manager", "company": "Software Company", "skills": ["Product Development", "Strategy", "Agile", "Market Analysis", "Leadership"], "location": "Bangalore"},
    {"id": 15, "title": "Financial Analyst", "company": "Bank", "skills": ["Investment Banking", "Equity Research", "Financial Modeling", "Valuation"], "location": "Chennai"},
    {"id": 16, "title": "UI/UX Designer", "company": "Software Company", "skills": ["Figma", "Sketch", "Adobe XD", "User Research", "Wireframing"], "location": "Mumbai"},
    {"id": 17, "title": "Cloud Architect", "company": "IT Company", "skills": ["Azure", "GCP", "AWS", "Cloud Architecture", "Migration"], "location": "Coimbatore"},
    {"id": 18, "title": "Technical Writer", "company": "Software Company", "skills": ["Documentation", "API", "Software Development Life Cycle", "Editing"], "location": "Bangalore"},
    {"id": 19, "title": "Compliance Officer", "company": "Bank", "skills": ["Regulatory Compliance", "Risk Management", "Legal Framework", "Auditing"], "location": "Chennai"},
    {"id": 20, "title": "HR Manager", "company": "Bank", "skills": ["Recruitment", "Employee Relations", "Payroll", "Training", "HR Strategy"], "location": "Mumbai"},
    {"id": 21, "title": "Systems Administrator", "company": "IT Company", "skills": ["Linux", "Windows Server", "Virtualization", "System Administration", "Troubleshooting"], "location": "Coimbatore"},
    {"id": 22, "title": "Digital Marketing Specialist", "company": "Software Company", "skills": ["SEO", "SEM", "Social Media Marketing", "Content Marketing", "Analytics"], "location": "Bangalore"},
    {"id": 23, "title": "Relationship Manager", "company": "Bank", "skills": ["Client Handling", "Sales", "Banking Products", "Relationship Building", "Communication"], "location": "Chennai"},
    {"id": 24, "title": "Software Architect", "company": "IT Company", "skills": ["System Design", "Scalability", "Leadership", "Enterprise Architecture", "Strategy"], "location": "Mumbai"},
    {"id": 25, "title": "Risk Analyst", "company": "Bank", "skills": ["Market Risk", "Credit Risk", "Regulatory Reporting", "Data Analysis", "Risk Management"], "location": "Coimbatore"},
    {"id": 26, "title": "Software Developer", "company": "IT Company", "skills": ["Python", "Java", "Cloud", "Agile", "DevOps"], "location": "Coimbatore"},
    {"id": 27, "title": "Frontend Engineer", "company": "Software Company", "skills": ["React", "Angular", "JavaScript", "HTML", "CSS"], "location": "Bangalore"},
    {"id": 28, "title": "Data Scientist", "company": "IT Company", "skills": ["Machine Learning", "SQL", "R", "Python", "Data Visualization"], "location": "Chennai"},
    {"id": 29, "title": "Cybersecurity Analyst", "company": "IT Company", "skills": ["Network Security", "Ethical Hacking", "Firewall", "Cryptography"], "location": "Mumbai"},
    {"id": 30, "title": "Bank Manager", "company": "Bank", "skills": ["Finance", "Leadership", "Customer Service", "Operations", "Compliance"], "location": "Coimbatore"},
    {"id": 31, "title": "Credit Analyst", "company": "Bank", "skills": ["Financial Modeling", "Risk Assessment", "Credit Analysis", "Accounting"], "location": "Bangalore"},
    {"id": 32, "title": "Full Stack Developer", "company": "Software Company", "skills": ["Node.js", "MongoDB", "React", "Express", "Full Stack Development"], "location": "Chennai"},
    {"id": 33, "title": "DevOps Engineer", "company": "IT Company", "skills": ["AWS", "Docker", "Kubernetes", "CI/CD", "Automation"], "location": "Mumbai"},
    {"id": 34, "title": "Mobile App Developer", "company": "Software Company", "skills": ["iOS", "Android", "Swift", "Kotlin", "Mobile UI/UX"], "location": "Coimbatore"},
    {"id": 35, "title": "Database Administrator", "company": "IT Company", "skills": ["SQL", "Oracle", "MongoDB", "Database Management", "Backup"], "location": "Bangalore"},
    {"id": 36, "title": "Business Analyst", "company": "Bank", "skills": ["Data Analysis", "Project Management", "Stakeholder Communication", "Process Improvement"], "location": "Chennai"},
    {"id": 37, "title": "QA Engineer", "company": "Software Company", "skills": ["Manual Testing", "Automation Testing", "Selenium", "QA Methodology", "Agile"], "location": "Mumbai"},
    {"id": 38, "title": "Network Engineer", "company": "IT Company", "skills": ["Cisco", "Juniper", "Cloud Networking", "TCP/IP", "Network Troubleshooting"], "location": "Coimbatore"},
    {"id": 39, "title": "Product Manager", "company": "Software Company", "skills": ["Product Development", "Strategy", "Agile", "Market Analysis", "Leadership"], "location": "Bangalore"},
    {"id": 40, "title": "Financial Analyst", "company": "Bank", "skills": ["Investment Banking", "Equity Research", "Financial Modeling", "Valuation"], "location": "Chennai"},
    {"id": 41, "title": "UI/UX Designer", "company": "Software Company", "skills": ["Figma", "Sketch", "Adobe XD", "User Research", "Wireframing"], "location": "Mumbai"},
    {"id": 42, "title": "Cloud Architect", "company": "IT Company", "skills": ["Azure", "GCP", "AWS", "Cloud Architecture", "Migration"], "location": "Coimbatore"},
    {"id": 43, "title": "Technical Writer", "company": "Software Company", "skills": ["Documentation", "API", "Software Development Life Cycle", "Editing"], "location": "Bangalore"},
    {"id": 44, "title": "Compliance Officer", "company": "Bank", "skills": ["Regulatory Compliance", "Risk Management", "Legal Framework", "Auditing"], "location": "Chennai"},
    {"id": 45, "title": "HR Manager", "company": "Bank", "skills": ["Recruitment", "Employee Relations", "Payroll", "Training", "HR Strategy"], "location": "Mumbai"},
    {"id": 46, "title": "Systems Administrator", "company": "IT Company", "skills": ["Linux", "Windows Server", "Virtualization", "System Administration", "Troubleshooting"], "location": "Coimbatore"},
    {"id": 47, "title": "Digital Marketing Specialist", "company": "Software Company", "skills": ["SEO", "SEM", "Social Media Marketing", "Content Marketing", "Analytics"], "location": "Bangalore"},
    {"id": 48, "title": "Relationship Manager", "company": "Bank", "skills": ["Client Handling", "Sales", "Banking Products", "Relationship Building", "Communication"], "location": "Chennai"},
    {"id": 49, "title": "Software Architect", "company": "IT Company", "skills": ["System Design", "Scalability", "Leadership", "Enterprise Architecture", "Strategy"], "location": "Mumbai"},
    {"id": 50, "title": "Risk Analyst", "company": "Bank", "skills": ["Market Risk", "Credit Risk", "Regulatory Reporting", "Data Analysis", "Risk Management"], "location": "Coimbatore"}
  ]
}

def seed_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Seeding database...")
    
    for job in jobs_data['job_vacancies']:
        company_name = job['company']
        
        # 1. Check/Create Company User
        # Simple logic: Create a user for the company if not exists (based on name)
        # We'll use a sanitized version of company name for email
        sanitized_name = company_name.lower().replace(" ", "")
        company_email = f"recruit@{sanitized_name}.com"
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (company_email,))
        user_row = cursor.fetchone()
        
        if not user_row:
            cursor.execute('''INSERT INTO users (name, email, password, role) 
                              VALUES (?, ?, ?, ?)''', 
                           (company_name, company_email, 'password123', 'COMPANY'))
            user_id = cursor.lastrowid
            print(f"Created User: {company_name} ({company_email})")
        else:
            user_id = user_row[0]

        # 2. Check/Create Company Profile
        cursor.execute("SELECT id FROM companies WHERE user_id = ?", (user_id,))
        comp_row = cursor.fetchone()
        
        if not comp_row:
            cursor.execute("INSERT INTO companies (user_id, company_name) VALUES (?, ?)", (user_id, company_name))
            company_id = cursor.lastrowid
            print(f"Created Company Profile: {company_name}")
        else:
            company_id = comp_row[0]
            
        # 3. Insert Job
        skills_str = ", ".join(job['skills'])
        description = f"We are hiring a {job['title']} in {job['location']}. Join {company_name} to work on exciting projects."
        
        cursor.execute('''INSERT INTO jobs (company_id, title, description, required_skills, location, salary_range)
                          VALUES (?, ?, ?, ?, ?, ?)''',
                       (company_id, job['title'], description, skills_str, job['location'], "Competitive"))
        
    conn.commit()
    conn.close()
    print("Database seeded successfully with 50 jobs!")

if __name__ == "__main__":
    seed_db()
