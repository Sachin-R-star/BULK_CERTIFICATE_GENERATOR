import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class JobStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"
    FAILED = "FAILED"

class CertificateStatus(str, PyEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="Certificate of Completion")
    event_name = Column(String(255), nullable=False, default="Special Event")
    issuer_name = Column(String(255), nullable=False, default="Aerio Institute")
    issue_date = Column(String(50), nullable=False, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    
    status = Column(String(50), default=JobStatus.PENDING.value, nullable=False)
    total_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    certificates = relationship("CertificateRecord", back_populates="job", cascade="all, delete-orphan")

class CertificateRecord(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=True)
    certificate_code = Column(String(100), unique=True, nullable=False)
    
    status = Column(String(50), default=CertificateStatus.PENDING.value, nullable=False)
    file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="certificates")
