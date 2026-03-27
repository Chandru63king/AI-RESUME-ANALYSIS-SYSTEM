import sqlite3
import os
from ai_engine.job_matcher import JobMatchEngine

DATABASE = 'database/jobportal.db'

def debug_matching():
    matcher = JobMatchEngine()
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    jobs = conn.execute('SELECT * FROM jobs').fetchall()
    matcher.build_cache(jobs)
    
    # Mock resume data similar to what user had
    resume_data = {
        "text": "manual testing jira sql qa engineer with 1 year experience",
        "primary_skills": ["sql", "manual testing"],
        "secondary_skills": ["jira"],
        "job_titles": ["QA Engineer"],
        "experience_years": 1.0
    }
    
    print("Debug Matching Results:")
    print("-" * 50)
    
    for job in jobs:
        score_details = matcher.compute_formal_score(resume_data, dict(job))
        if score_details['match_score'] >= 40:
            print(f"Job: {job['title']} (ID: {job['id']})")
            print(f"  Final Score: {score_details['match_score']}")
            print(f"  Eligible: {score_details['eligible']}")
            print(f"  Breakdown: Skill={score_details['skill_score']}, Exp={score_details['exp_score']}, Title={score_details['title_score']}")
            print("-" * 30)

    conn.close()

if __name__ == "__main__":
    debug_matching()
