import csv
import io
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, CertificateRecord, JobStatus, CertificateStatus
from app.schemas import JobCreateRequest, JobResponse, JobProgressResponse, RecipientInput
from app.services.processor import process_job_background, create_job_zip_archive
from app.config import OUTPUT_DIR, DEFAULT_TITLE, DEFAULT_ORGANIZATION

router = APIRouter(prefix="/jobs", tags=["Certificate Jobs"])

def generate_certificate_code(index: int) -> str:
    """Generates a clean unique verification code for certificates."""
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"CERT-2026-{index:04d}-{unique_suffix}"

@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_bulk_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Accepts a bulk certificate generation request.
    Validates recipient details and queues generation job.
    """
    issue_date_str = request.issue_date or datetime.utcnow().strftime("%Y-%m-%d")

    # Create Job database record
    new_job = Job(
        title=request.title,
        event_name=request.event_name,
        issuer_name=request.issuer_name,
        issue_date=issue_date_str,
        status=JobStatus.PENDING.value,
        total_count=len(request.recipients),
        success_count=0,
        failed_count=0
    )
    db.add(new_job)
    db.flush()

    # Pre-create certificate records for each recipient
    for idx, recipient in enumerate(request.recipients, start=1):
        cert_code = generate_certificate_code(idx)
        cert_record = CertificateRecord(
            job_id=new_job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            certificate_code=cert_code,
            status=CertificateStatus.PENDING.value
        )
        db.add(cert_record)

    db.commit()
    db.refresh(new_job)

    # Queue background task for certificate rendering
    background_tasks.add_task(process_job_background, new_job.id)

    return new_job

@router.post("/csv", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_bulk_job_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(DEFAULT_TITLE),
    event_name: str = Form("Event Participant"),
    issuer_name: str = Form(DEFAULT_ORGANIZATION),
    issue_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts a CSV file upload containing recipients (name, email) and creates a bulk job.
    Supports flexible column headers: 'name', 'Name', 'recipient_name', 'Full Name', etc.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    contents = await file.read()
    try:
        decoded = contents.decode("utf-8-sig") # Handles UTF-8 with or without BOM
    except UnicodeDecodeError:
        decoded = contents.decode("latin-1")

    reader = csv.DictReader(io.StringIO(decoded))
    recipients: List[RecipientInput] = []
    errors = []

    for idx, row in enumerate(reader, start=1):
        # Case-insensitive & flexible header resolution
        name = None
        email = None

        for k, v in row.items():
            if not k:
                continue
            key_clean = k.strip().lower().replace("_", " ")
            if key_clean in ["name", "recipient name", "full name", "participant name"]:
                name = v
            elif key_clean in ["email", "email address", "recipient email"]:
                email = v

        if not name or not name.strip():
            errors.append(f"Row {idx}: Name is missing")
            continue

        try:
            rec = RecipientInput(name=name.strip(), email=email.strip() if email else None)
            recipients.append(rec)
        except Exception as e:
            errors.append(f"Row {idx} ({name}): {str(e)}")

    if not recipients:
        raise HTTPException(
            status_code=422,
            detail={"message": "No valid recipients found in CSV file.", "errors": errors}
        )

    # Create job request payload
    job_req = JobCreateRequest(
        title=title,
        event_name=event_name,
        issuer_name=issuer_name,
        issue_date=issue_date,
        recipients=recipients
    )

    return create_bulk_job(request=job_req, background_tasks=background_tasks, db=db)

@router.get("", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    """List all certificate generation jobs."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return jobs

@router.get("/{job_id}", response_model=JobResponse)
def get_job_details(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full status, progress metrics, and individual recipient certificates for a job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found")
    return job

@router.get("/{job_id}/progress", response_model=JobProgressResponse)
def get_job_progress(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves quick job progress percentage and current status summary.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found")

    progress = 0.0
    if job.total_count > 0:
        processed = job.success_count + job.failed_count
        progress = round((processed / job.total_count) * 100.0, 2)
        if job.status == JobStatus.COMPLETED.value:
            progress = 100.0

    return JobProgressResponse(
        id=job.id,
        title=job.title,
        event_name=job.event_name,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress_percentage=progress,
        created_at=job.created_at,
        completed_at=job.completed_at
    )

@router.get("/{job_id}/download-all")
def download_all_certificates_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Downloads a ZIP file containing all successfully generated certificates for a job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{job_id}' not found")

    if job.success_count == 0:
        raise HTTPException(status_code=400, detail="No certificates available to download for this job.")

    # Ensure ZIP archive is created
    zip_file_path = create_job_zip_archive(job_id)
    if not zip_file_path or not FileResponse:
        raise HTTPException(status_code=404, detail="ZIP archive file not found.")

    filename = f"job_{job_id[:8]}_certificates.zip"
    return FileResponse(
        path=zip_file_path,
        media_type="application/zip",
        filename=filename
    )
