import pytest
from pydantic import ValidationError
from app.schemas import RecipientInput, JobCreateRequest

def test_valid_recipient_input():
    recipient = RecipientInput(name="  John Doe  ", email="john@example.com")
    assert recipient.name == "John Doe"
    assert recipient.email == "john@example.com"

def test_invalid_recipient_empty_name():
    with pytest.raises(ValidationError) as excinfo:
        RecipientInput(name="   ", email="john@example.com")
    assert "Recipient name cannot be empty or blank" in str(excinfo.value)

def test_invalid_email_format():
    with pytest.raises(ValidationError) as excinfo:
        RecipientInput(name="John Doe", email="invalid-email-address")
    assert "Invalid email address format" in str(excinfo.value)

def test_empty_recipients_list_job_request():
    with pytest.raises(ValidationError):
        JobCreateRequest(
            title="Course Certificate",
            event_name="Python 101",
            recipients=[]
        )
