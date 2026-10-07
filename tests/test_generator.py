import os
import pytest
from app.services.generator import generate_pdf_certificate

def test_generate_pdf_certificate_success(tmp_path):
    job_id = "test-job-123"
    cert_id = "test-cert-456"
    recipient_name = "Jane Smith"
    event_name = "FastAPI Masterclass"
    issuer_name = "Aerio Academy"
    issue_date = "2026-10-07"
    cert_code = "CERT-TEST-0001"

    pdf_path = generate_pdf_certificate(
        job_id=job_id,
        certificate_id=cert_id,
        recipient_name=recipient_name,
        event_name=event_name,
        issuer_name=issuer_name,
        issue_date=issue_date,
        certificate_code=cert_code
    )

    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")

    # Read binary header to confirm valid PDF magic bytes
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

def test_generate_pdf_certificate_simulated_failure():
    with pytest.raises(ValueError) as excinfo:
        generate_pdf_certificate(
            job_id="job-fail",
            certificate_id="cert-fail",
            recipient_name="Fail Recipient __TRIGGER_FAIL__",
            event_name="Failing Event",
            issuer_name="Aerio",
            issue_date="2026-10-07",
            certificate_code="CERT-FAIL-0001"
        )
    assert "Simulated generation failure" in str(excinfo.value)
