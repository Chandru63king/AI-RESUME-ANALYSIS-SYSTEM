
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from ai_engine.job_matcher import JobMatchEngine

def verify_100_match():
    print("--- Starting 100% Match Logic Verification ---")
    
    matcher = JobMatchEngine()
    
    # Perfectly Matched Resume
    perfect_resume = {
        "text": "Senior Python Developer with 5 years of experience. Expert in AWS, Docker, Kubernetes, and SQL. Bachelor of Technology in Computer Science. Lead Developer at TechSolutions.",
        "skills": ["Python", "AWS", "Docker", "Kubernetes", "SQL", "Git", "Linux", "REST API"],
        "primary_skills": ["Python", "AWS", "Docker", "Kubernetes"],
        "secondary_skills": ["SQL", "Git", "Linux", "REST API"],
        "education": "Bachelor of Technology",
        "experience_years": 5.0,
        "job_titles": ["Senior Python Developer", "Lead Developer"],
        "primary_domain": "Software Engineering"
    }

    # Job specifically requiring these attributes
    perfect_job = {
        "title": "Senior Python Developer",
        "description": "We are looking for a Senior Python Developer with 5+ years of experience. Must have expertise in AWS, Docker, and Kubernetes. Engineering degree required.",
        "required_skills": "Python, AWS, Docker, Kubernetes",
        "category": "Software Engineering",
        "company_name": "Perfect Match Corp"
    }
    
    print("\n[Test] Computing Match Score for Perfect Pair...")
    result = matcher.compute_formal_score(perfect_resume, perfect_job)
    
    print(f"Match Score: {result['match_score']}%")
    print(f"Skill Score: {result['skill_score']}%")
    print(f"Exp Score: {result['exp_score']}%")
    print(f"Edu Score: {result['edu_score']}%")
    print(f"Title Score: {result['title_score']}%")
    
    if result['match_score'] >= 100:
        print("\nSUCCESS: Achieved 100% match score!")
    else:
        print(f"\nFAILURE: Match score is {result['match_score']}%, expected 100%.")

    # Test Grace Threshold (4.5 years exp for 5 yr job)
    print("\n[Test] Computing Match Score for Grace Period (4.5 yrs exp for 5 yr job)...")
    perfect_resume['experience_years'] = 4.5
    result_grace = matcher.compute_formal_score(perfect_resume, perfect_job)
    print(f"Exp Score (Grace): {result_grace['exp_score']}%")
    if result_grace['exp_score'] >= 100:
        print("SUCCESS: Grace period correctly gave 100% exp score.")
    else:
        print(f"FAILURE: Grace period gave {result_grace['exp_score']}%.")

if __name__ == "__main__":
    verify_100_match()
