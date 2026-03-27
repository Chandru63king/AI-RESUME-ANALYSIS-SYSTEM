
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from ai_engine.resume_parser import ResumeParser
from ai_engine.job_matcher import JobMatchEngine

def verify_ats():
    print("--- Starting ATS Logic Verification ---")
    
    parser = ResumeParser()
    matcher = JobMatchEngine()
    
    # Mock Data: Strong Candidate
    strong_candidate = {
        "text": "Experienced Software Engineer with Python, Java, AWS, Docker, Kubernetes. Bachelor of Technology. Led team of 5 developers.",
        "skills": ["Python", "Java", "AWS", "Docker", "Kubernetes", "SQL"],
        "primary_skills": ["Python", "Java", "AWS"],
        "secondary_skills": ["Docker", "Kubernetes", "SQL"],
        "education": "Bachelor of Technology",
        "experience_years": 5.0,
        "job_titles": ["Software Engineer"],
        "certifications": "AWS Certified"
    }

    # Mock Data: Weak Candidate
    weak_candidate = {
        "text": "Fresh graduate looking for opportunity. Basic knowledge of C.",
        "skills": ["C"],
        "primary_skills": [],
        "secondary_skills": ["C"],
        "education": "Not specified",
        "experience_years": 0.0,
        "job_titles": [],
        "certifications": "None"
    }

    print("\n[Test 1] Parser ATS Score (General Readiness)...")
    score_strong = parser.calculate_ats_score(strong_candidate)
    score_weak = parser.calculate_ats_score(weak_candidate)
    
    print(f"Strong Candidate Score: {score_strong}/100 (Expected > 80)")
    print(f"Weak Candidate Score: {score_weak}/100 (Expected < 40)")
    
    # Mock Job for Matching
    mock_job = {
        "title": "Senior Software Engineer",
        "description": "Looking for 5+ years exp in Python, AWS. Degree required.",
        "required_skills": "Python, AWS, Docker, Kubernetes",
        "company_name": "Tech Corp"
    }
    
    print("\n[Test 2] Job Matcher Formal Score (Specific Job)...")
    match_result = matcher.compute_formal_score(strong_candidate, mock_job)
    
    print(f"Match Score: {match_result['match_score']}%")
    print(f"Breakdown: Skill={match_result['skill_score']}, Exp={match_result['exp_score']}, Edu={match_result['edu_score']}, Title={match_result['title_score']}")
    
    if match_result['match_score'] > 70:
        print("✅ Correctly identified strong match.")
    else:
        print("❌ Failed to identify strong match.")

if __name__ == "__main__":
    verify_ats()
