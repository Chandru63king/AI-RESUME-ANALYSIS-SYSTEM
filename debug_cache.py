
import sqlite3
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from ai_engine.job_matcher import JobMatchEngine

DATABASE = 'database/jobportal.db'
matcher = JobMatchEngine()

def debug_cache():
    try:
        print("Connecting to DB...")
        if not os.path.exists(DATABASE):
            print(f"Error: Database file {DATABASE} not found.")
            return

        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        
        print("Fetching jobs...")
        jobs = db.execute('SELECT * FROM jobs').fetchall()
        print(f"Loaded {len(jobs)} jobs.")
        
        if not jobs:
            print("No jobs found in DB. Skipping cache build.")
            return

        print("Building cache...")
        matcher.build_cache(jobs)
        print("Cache built successfully.")
        
        # Test a small match
        print("Testing a sample match...")
        sample_resume = {"text": "python developer", "primary_skills": ["python"], "experience_years": 2}
        results = matcher.get_top_matches(sample_resume, threshold=0)
        print(f"Found {len(results)} matches.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_cache()
