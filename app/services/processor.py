import zipfile
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Job, CertificateRecord, JobStatus, CertificateStatus
from app.services.generator import generate_pdf_certificate
from app.config import OUTPUT_DIR

def process_job_background(job_id: str):
    """
    Background worker function that iterates through all pending certificate records of a job,
    generates individual PDF certificates, tracks successes & failures, and updates job status.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.PROCESSING.value
        db.commit()

        certificates = db.query(CertificateRecord).filter(CertificateRecord.job_id == job_id).all()
        
        success_count = 0
        failed_count = 0

        for cert in certificates:
            try:
                # Generate PDF for this certificate
                pdf_path = generate_pdf_certificate(
                    job_id=job.id,
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    event_name=job.event_name,
                    issuer_name=job.issuer_name,
                    issue_date=job.issue_date,
                    certificate_code=cert.certificate_code
                )
                cert.status = CertificateStatus.SUCCESS.value
                cert.file_path = pdf_path
                cert.error_message = None
                success_count += 1
            except Exception as e:
                cert.status = CertificateStatus.FAILED.value
                cert.error_message = str(e)
                failed_count += 1
            
            db.commit()

        # Update final job summary status
        job.success_count = success_count
        job.failed_count = failed_count
        job.completed_at = datetime.utcnow()

        if failed_count == 0:
            job.status = JobStatus.COMPLETED.value
        elif success_count > 0 and failed_count > 0:
            job.status = JobStatus.PARTIALLY_FAILED.value
        else:
            job.status = JobStatus.FAILED.value

        db.commit()

        # Optionally bundle all successfully generated PDFs into a ZIP archive
        if success_count > 0:
            create_job_zip_archive(job.id)

    except Exception as exc:
        if 'job' in locals() and job:
            job.status = JobStatus.FAILED.value
            db.commit()
    finally:
        db.close()

def create_job_zip_archive(job_id: str) -> str:
    """
    Bundles all generated PDF certificates of a job into a ZIP archive.
    """
    job_dir = Path(OUTPUT_DIR) / job_id
    zip_path = job_dir / f"certificates_job_{job_id[:8]}.zip"
    
    if not job_dir.exists():
        return ""

    pdf_files = list(job_dir.glob("*.pdf"))
    if not pdf_files:
        return ""

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_file in pdf_files:
            zipf.write(pdf_file, arcname=pdf_file.name)

    return str(zip_path)
