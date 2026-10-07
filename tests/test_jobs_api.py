import time
from fastapi.testclient import TestClient
from main import app
from app.services.processor import process_job_background

client = TestClient(app)

def test_create_bulk_job_json():
    payload = {
        "title": "Certificate of Excellence",
        "event_name": "Python & FastAPI Hackathon",
        "issuer_name": "Aerio Tech",
        "recipients": [
            {"name": "Alice Wonderland", "email": "alice@example.com"},
            {"name": "Bob Builder", "email": "bob@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    
    assert "id" in data
    assert data["total_count"] == 2
    assert data["status"] == "PENDING"
    assert len(data["certificates"]) == 2

    # Process job synchronously
    job_id = data["id"]
    process_job_background(job_id)

    # Check job status after background processing
    job_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 0

def test_job_with_individual_failure():
    payload = {
        "title": "Certificate of Participation",
        "event_name": "Resilience Testing Workshop",
        "issuer_name": "Aerio Tech",
        "recipients": [
            {"name": "Good Recipient 1", "email": "good1@example.com"},
            {"name": "Bad Recipient __TRIGGER_FAIL__", "email": "bad@example.com"},
            {"name": "Good Recipient 2", "email": "good2@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]

    # Process job synchronously
    process_job_background(job_id)

    # Fetch updated job status
    job_resp = client.get(f"/api/v1/jobs/{job_id}")
    job_data = job_resp.json()

    assert job_data["status"] == "PARTIALLY_FAILED"
    assert job_data["total_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 1

    # Verify failure detail on the broken recipient
    failed_cert = next(c for c in job_data["certificates"] if "__TRIGGER_FAIL__" in c["recipient_name"])
    assert failed_cert["status"] == "FAILED"
    assert "Simulated generation failure" in failed_cert["error_message"]

def test_create_bulk_job_csv():
    csv_content = "name,email\nRecipient One,one@example.com\nRecipient Two,two@example.com\n"
    files = {"file": ("recipients.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {
        "title": "CSV Event Certificate",
        "event_name": "Data Analysis Workshop"
    }

    response = client.post("/api/v1/jobs/csv", files=files, data=data)
    assert response.status_code == 202
    res_data = response.json()
    assert res_data["total_count"] == 2
    assert res_data["event_name"] == "Data Analysis Workshop"
