import requests
import os

def test_resume_scan():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()

    # 1. Login
    print("Testing Login...")
    login_data = {
        "email": "seeker@example.com",
        "password": "seeker123"
    }
    response = session.post(f"{base_url}/login", data=login_data)
    if response.status_code == 200 and "Dashboard" in response.text:
        print("[SUCCESS] Login Successful")
    else:
        print(f"[ERROR] Login Failed: {response.status_code}")
        # print(response.text)
        return

    # 2. Upload Resume
    print("\nTesting Resume Upload...")
    resume_path = r"c:\Users\ELCOT\OneDrive\Desktop\chandru12\uploads\13_6_Arun_Kumar_Demo_QA_Resume.pdf"
    if not os.path.exists(resume_path):
        print(f"[ERROR] Test resume not found at {resume_path}")
        return

    with open(resume_path, 'rb') as f:
        files = {'file': f}
        response = session.post(f"{base_url}/api/upload_resume", files=files)

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("[SUCCESS] Resume Upload & Analysis Successful")
            print(f"   Domain: {data['analysis'].get('domain')}")
            print(f"   Level: {data['analysis'].get('level')}")
            print(f"   Skills: {data['analysis'].get('skills')}")
            print(f"   Matches Found: {len(data.get('recommendations', []))}")
            if data.get('recommendations'):
                print(f"   Top Match: {data['recommendations'][0].get('title')} ({data['recommendations'][0].get('match_score')}% Match)")
            else:
                print("   [INFO] No matches met the 50% threshold.")
        else:
            print(f"❌ API returned success=False: {data.get('error')}")
    else:
        print(f"❌ API Request Failed with status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_resume_scan()
