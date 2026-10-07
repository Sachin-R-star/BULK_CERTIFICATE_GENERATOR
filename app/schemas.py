from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RecipientInput(BaseModel):
    name: str = Field(..., description="Recipient full name", min_length=1)
    email: Optional[str] = Field(None, description="Recipient email address")

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Recipient name cannot be empty or blank")
        return v.strip()

    @field_validator("email")
    def validate_email(cls, v):
        if v is not None and v.strip() != "":
            v = v.strip()
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError(f"Invalid email address format: '{v}'")
        return v

class JobCreateRequest(BaseModel):
    title: str = Field("Certificate of Completion", description="Certificate title")
    event_name: str = Field("Python Backend Bootcamp 2026", description="Event or Course Name")
    issuer_name: str = Field("Aerio Institute", description="Issuing Organization Name")
    issue_date: Optional[str] = Field(None, description="Issue Date (YYYY-MM-DD), default is current date")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipients")

    @field_validator("title", "event_name", "issuer_name")
    def validate_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: Optional[str] = None
    certificate_code: str
    status: str
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

class JobProgressResponse(BaseModel):
    id: str
    title: str
    event_name: str
    status: str
    total_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    completed_at: Optional[datetime] = None

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    event_name: str
    issuer_name: str
    issue_date: str
    status: str
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    certificates: List[CertificateResponse] = []
