from fastapi.testclient import TestClient
from main import app
from app.services.processor import process_job_background

client = TestClient(app)

def test_certificate_download_and_verification():
    payload = {
        "title": "Certificate of Completion",
        "event_name": "API Design Mastery",
        "issuer_name": "Aerio Institute",
        "recipients": [
            {"name": "Download Tester", "email": "tester@example.com"}
        ]
    }

    # 1. Create job
    create_resp = client.post("/api/v1/jobs", json=payload)
    assert create_resp.status_code == 202
    job_id = create_resp.json()["id"]

    # 2. Process job
    process_job_background(job_id)

    # 3. Get certificate details
    job_resp = client.get(f"/api/v1/jobs/{job_id}")
    cert = job_resp.json()["certificates"][0]
    cert_id = cert["id"]
    cert_code = cert["certificate_code"]

    # 4. Fetch certificate metadata
    cert_resp = client.get(f"/api/v1/certificates/{cert_id}")
    assert cert_resp.status_code == 200
    assert cert_resp.json()["recipient_name"] == "Download Tester"

    # 5. Download certificate PDF
    dl_resp = client.get(f"/api/v1/certificates/{cert_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert dl_resp.content.startswith(b"%PDF-")

    # 6. Verify certificate by code
    verify_resp = client.get(f"/api/v1/certificates/verify/{cert_code}")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["valid"] is True
    assert v_data["recipient_name"] == "Download Tester"
    assert v_data["event_name"] == "API Design Mastery"

    # 7. Download ZIP file for entire job
    zip_resp = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert zip_resp.status_code == 200
    assert zip_resp.headers["content-type"] == "application/zip"
