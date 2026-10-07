import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CertificateRecord, CertificateStatus
from app.schemas import CertificateResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])

@router.get("/{cert_id}", response_model=CertificateResponse)
def get_certificate_details(cert_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata details of a specific certificate."""
    cert = db.query(CertificateRecord).filter(CertificateRecord.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID '{cert_id}' not found")
    return cert

@router.get("/{cert_id}/download")
def download_certificate(cert_id: str, db: Session = Depends(get_db)):
    """Download the generated PDF file for an individual certificate."""
    cert = db.query(CertificateRecord).filter(CertificateRecord.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID '{cert_id}' not found")

    if cert.status != CertificateStatus.SUCCESS.value or not cert.file_path:
        raise HTTPException(
            status_code=400,
            detail=f"Certificate generation is not complete or failed. Status: {cert.status}. Error: {cert.error_message}"
        )

    if not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="Certificate PDF file not found on server disk.")

    safe_name = cert.recipient_name.replace(" ", "_")
    filename = f"Certificate_{safe_name}_{cert.certificate_code}.pdf"

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=filename
    )

@router.get("/verify/{certificate_code}")
def verify_certificate_code(certificate_code: str, db: Session = Depends(get_db)):
    """
    Public verification endpoint to check the authenticity of a certificate by code.
    """
    cert = db.query(CertificateRecord).filter(CertificateRecord.certificate_code == certificate_code).first()
    if not cert:
        return {
            "valid": False,
            "message": f"No certificate found with code '{certificate_code}'"
        }

    return {
        "valid": cert.status == CertificateStatus.SUCCESS.value,
        "certificate_code": cert.certificate_code,
        "recipient_name": cert.recipient_name,
        "recipient_email": cert.recipient_email,
        "event_name": cert.job.event_name if cert.job else None,
        "issuer_name": cert.job.issuer_name if cert.job else None,
        "issue_date": cert.job.issue_date if cert.job else None,
        "status": cert.status,
        "download_url": f"/api/v1/certificates/{cert.id}/download" if cert.status == CertificateStatus.SUCCESS.value else None
    }
