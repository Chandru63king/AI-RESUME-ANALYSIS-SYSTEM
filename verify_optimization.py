
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from ai_engine.job_matcher import JobMatchEngine
from ai_engine.resume_parser import ResumeParser

def test_matcher():
    print("--- Testing JobMatchEngine ---")
    matcher = JobMatchEngine()
    
    # Mock Jobs
    jobs = [
        {
            "id": 1,
            "title": "Senior Python Developer",
            "company_name": "Tech Corp",
            "description": "We need a Senior Python Developer with 5+ years experience. Must know Django, Flask, and AWS.",
            "required_skills": "python, django, flask, aws",
            "location": "New York"
        },
        {
            "id": 2,
            "title": "Junior Web Developer",
            "company_name": "StartUp Inc",
            "description": "Looking for a Junior Web Developer with 1 year experience in HTML, CSS, JS.",
            "required_skills": "html, css, javascript",
            "location": "Remote"
        },
        {
            "id": 3,
            "title": "Data Scientist",
            "company_name": "AI Labs",
            "description": "Data Scientist needed. Python, Machine Learning, Pandas required.",
            "required_skills": "python, machine learning, pandas",
            "location": "San Francisco"
        }
    ]
    
    print(f"Building cache for {len(jobs)} jobs...")
    matcher.build_cache(jobs)
    
    # Test Resume 1: Senior Python Dev
    resume_1 = {
        "text": "Experienced Python Developer with 6 years of experience in Django, Flask, and Cloud computing.",
        "skills": ["python", "django", "flask", "aws"],
        "experience_years": 6
    }
    
    matches_1 = matcher.get_top_matches(resume_1, threshold=70)
    print(f"\nResume 1 (Senior Python, 6yr): Found {len(matches_1)} matches")
    for m in matches_1:
        print(f" - {m['title']} ({m['match_score']}%) - Reasons: {m['reasons']}")
        
    # Check if Job 1 is top match
    if matches_1 and matches_1[0]['id'] == 1:
        print("PASS: Correctly identified Senior Python Dev job.")
    else:
        print("FAIL: Did not recommend Senior Python Dev job.")

    # Test Resume 2: Junior Python (Should fail strict experience for Senior role?)
    resume_2 = {
        "text": "Junior Python developer with 1 year experience.",
        "skills": ["python", "django"],
        "experience_years": 1
    }
    matches_2 = matcher.get_top_matches(resume_2, threshold=70)
    print(f"\nResume 2 (Junior Python, 1yr): Found {len(matches_2)} matches")
    # Should NOT match Job 1 (Requires 5+ years)
    if not any(m['id'] == 1 for m in matches_2):
         print("PASS: Correctly filtered out Senior role for Junior resume (Experience).")
    else:
         print("FAIL: Recommended Senior role to Junior.")

def test_parser_cleaning():
    print("\n--- Testing ResumeParser Cleaning ---")
    parser = ResumeParser()
    dirty_text = "Python   Developer\u00a0with 5 years of experience."
    cleaned = parser.clean_text(dirty_text)
    print(f"Original: '{dirty_text}'")
    print(f"Cleaned:  '{cleaned}'")
    
    if cleaned == "python developer with 5 years of experience":
        print("PASS: Text cleaning works.")
    else:
        print("FAIL: Text cleaning failed.")

if __name__ == "__main__":
    try:
        test_matcher()
        test_parser_cleaning()
    except Exception as e:
        print(f"ERROR: {e}")
