import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/certificates.db")

# Output folder for generated certificate PDFs and ZIP files
OUTPUT_DIR = BASE_DIR / "generated_certificates"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Certificate default configurations
DEFAULT_ORGANIZATION = "Aerio Learning Institute"
DEFAULT_TITLE = "Certificate of Completion"
