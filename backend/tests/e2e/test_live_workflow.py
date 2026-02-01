import pytest
import time
from fastapi.testclient import TestClient

@pytest.mark.live
def test_live_e2e_workflow(test_client: TestClient):
    """
    Test the full workflow against LIVE APIs (OpenAI, Neo4j).
    This test requires environment variables to be set.
    """
    print("\nStarting Live E2E Workflow Test...")
    
    # 1. Create Session
    print("1. Creating Session...")
    response = test_client.post("/api/v1/session")
    assert response.status_code == 201
    session_data = response.json()
    session_id = session_data["session_id"]
    headers = {"X-Session-ID": session_id}
    print(f"   Session Created: {session_id}")

    # 2. Upload Resume
    print("2. Uploading Resume...")
    resume_text = """
    Jane Doe
    Software Engineer
    Email: jane@example.com
    
    Skills: Python, TypeScript, React, Docker, AWS
    
    Experience:
    Senior Software Engineer at Tech Corp (2020-Present)
    - Built microservices using Python and FastAPI
    - Deployed to AWS utilizing Docker and Kubernetes
    - Mentored junior developers
    
    Education:
    BS Computer Science, University of Technology (2019)
    """
    
    files = {
        "file": ("resume.txt", resume_text, "text/plain")
    }
    
    response = test_client.post("/api/v1/upload/resume", files=files, headers=headers)
    assert response.status_code == 200
    resume_data = response.json()
    resume_id = resume_data["resume_id"]
    print(f"   Resume Uploaded: {resume_id}")
    assert len(resume_data["skills"]) > 0 
    print(f"   Parsed {len(resume_data['skills'])} skills")
    
    # 3. Upload Job Description
    print("3. Uploading Job Description...")
    jd_text = """
    Senior Software Engineer
    Tech Solutions Inc.
    
    We are looking for a Senior Software Engineer with:
    - Strong Python and TypeScript skills
    - Experience with cloud platforms (AWS/GCP)
    - Knowledge of containerization (Docker/Kubernetes)
    
    Nice to have:
    - GraphQL
    - Machine Learning
    """
    
    response = test_client.post(
        "/api/v1/upload/job-description", 
        data={"text": jd_text}, 
        headers=headers
    )
    assert response.status_code == 200
    jd_data = response.json()
    job_id = jd_data["job_id"]
    print(f"   JD Uploaded: {job_id}")
    
    # 4. Start Analysis
    print("4. Starting Analysis (this may take 30-60s)...")
    # Note: TestClient waits for background tasks to complete
    start_time = time.time()
    response = test_client.post(
        "/api/v1/analyze", 
        json={"session_id": session_id},
        headers=headers
    )
    assert response.status_code == 200
    analysis_data = response.json()
    assert analysis_data["status"] == "started"
    print(f"   Analysis Request Accepted. Analysis ID: {analysis_data['analysis_id']}")
    
    # 5. Verify Results
    print("5. Verifying Results...")
    # Fetch results to confirm completion (since TestClient waited, it should be done)
    response = test_client.get(f"/api/v1/results/{session_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    print(f"   Status: {data['status']}")
    if data["status"] == "failed":
        print(f"   Error: {data.get('error')}")
    
    assert data["status"] == "completed"
    assert len(data["job_matches"]) > 0
    match = data["job_matches"][0]
    print(f"   Fit Score: {match['fit_score']}")
    assert match["fit_score"] > 0
    assert len(match["matching_skills"]) > 0
    
    duration = time.time() - start_time
    print(f"\nLive E2E Test Completed in {duration:.2f} seconds.")
