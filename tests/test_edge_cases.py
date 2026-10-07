import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.processor import process_job_background
from app.services.generator import generate_pdf_certificate

client = TestClient(app)

def test_very_long_recipient_name(tmp_path):
    long_name = "Dr. Christopher Bartholomew Alexander Montgomery III, Senior Principal Backend Architect"
    pdf_path = generate_pdf_certificate(
        job_id="test-long-name",
        certificate_id="cert-long",
        recipient_name=long_name,
        event_name="Advanced Distributed Systems Masterclass 2026",
        issuer_name="International Institute of Advanced Software Engineering",
        issue_date="2026-10-07",
        certificate_code="CERT-LONG-0001"
    )
    assert pdf_path.endswith(".pdf")

def test_large_bulk_generation_job():
    recipients = [{"name": f"Recipient Number {i}", "email": f"user{i}@example.com"} for i in range(1, 51)]
    payload = {
        "title": "Bulk Load Test Certificate",
        "event_name": "High Scalability Performance Workshop",
        "issuer_name": "Aerio Tech",
        "recipients": recipients
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["id"]
    assert response.json()["total_count"] == 50

    # Process all 50 items synchronously
    process_job_background(job_id)

    job_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert job_resp.status_code == 200
    data = job_resp.json()
    assert data["status"] == "COMPLETED"
    assert data["success_count"] == 50
    assert data["failed_count"] == 0

def test_csv_flexible_column_headers():
    csv_data = "Full Name,Email Address\nAlice Green,alice.green@example.com\nBob Brown,bob.brown@example.com\n"
    files = {"file": ("flexible.csv", csv_data.encode("utf-8"), "text/csv")}
    
    response = client.post("/api/v1/jobs/csv", files=files, data={"event_name": "Flexible CSV Test"})
    assert response.status_code == 202
    assert response.json()["total_count"] == 2

def test_non_existent_job_returns_404():
    response = client.get("/api/v1/jobs/non-existent-uuid-12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_non_existent_certificate_returns_404():
    response = client.get("/api/v1/certificates/non-existent-cert-12345/download")
    assert response.status_code == 404
