# Bulk Certificate Generator API

A production-oriented FastAPI backend for bulk certificate generation with asynchronous processing, validation, job tracking, fault isolation, PDF generation, and certificate verification.

**Tech Stack:** Python • FastAPI • SQLAlchemy • SQLite • Pillow • Pytest • HTTPX

---

## 🌐 Live Deployment & Demo Links

- **Live Web Dashboard**: [https://bulk-certificate-generator-rhgm.onrender.com](https://bulk-certificate-generator-rhgm.onrender.com)
- **Interactive API Docs (Swagger)**: [https://bulk-certificate-generator-rhgm.onrender.com/docs](https://bulk-certificate-generator-rhgm.onrender.com/docs)
- **ReDoc API Specifications**: [https://bulk-certificate-generator-rhgm.onrender.com/redoc](https://bulk-certificate-generator-rhgm.onrender.com/redoc)

---

## 🌟 Key Features

- **Bulk Processing**: Accept JSON list payloads or flexible CSV file uploads (`name`, `Full Name`, `email`, `Email Address`, etc.).
- **High-Volume Tested**: Tested with 50+ certificates rendered in parallel in a single background job.
- **Asynchronous Background Worker**: Non-blocking job creation (HTTP 202 Accepted) with background execution (`BackgroundTasks`).
- **Dynamic Canvas Auto-Scaling**: Automatic font-size scaling prevents long recipient names (e.g., 80+ characters) or long event titles from overflowing canvas borders.
- **Fault-Tolerant Generation**: An error while rendering one recipient's certificate does **not** stop other valid certificates in the same job from being generated.
- **Granular Job Tracking**: Monitor real-time status (`PENDING`, `PROCESSING`, `COMPLETED`, `PARTIALLY_FAILED`, `FAILED`), success/failure counts, progress percentage, and error logs per recipient.
- **Multiple Retrieval Options**:
  - Download individual PDF certificates.
  - Download a single **ZIP archive** containing all generated PDF certificates for a job.
  - Public verification endpoint by certificate code (`CERT-2026-XXXX-XXXX`).
- **Interactive Web UI Dashboard & Swagger**: Built-in visual dashboard for instant manual testing at `http://localhost:8000/`.

---

## 🏗️ Architecture & Technology Stack

- **Language**: Python 3.8+
- **Web Framework**: FastAPI (Async support, auto Swagger/OpenAPI docs, Pydantic data validation)
- **Database & ORM**: SQLite + SQLAlchemy 2.0 (Relational persistence)
- **Certificate Rendering**: Pillow (High-resolution vector-quality PDF output)
- **Testing**: Pytest + HTTPX TestClient

---

## 🚀 Quick Setup & Installation

### 1. Clone & Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/Sachin-R-star/BULK_CERTIFICATE_GENERATOR.git
cd BULK_CERTIFICATE_GENERATOR

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
.\venv\Scripts\activate.bat

# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Application

Start the Uvicorn server:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Interactive Web Dashboard**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **Swagger API Documentation**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **ReDoc API Documentation**: Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

---

## 🧪 Running Comprehensive Tests

The test suite contains **15 automated tests** covering input validation, PDF rendering, dynamic font auto-scaling, high-volume load processing (50+ items), CSV flexibility, job status polling, individual failure isolation, HTTP 404 edge cases, and certificate/ZIP retrieval.

```bash
pytest -v
```

---

## 📖 API Usage Guide

### 1. Submit a Bulk Certificate Request (JSON Payload)

**Endpoint**: `POST /api/v1/jobs`  
**Response Code**: `202 Accepted`

```bash
curl -X POST "https://bulk-certificate-generator-rhgm.onrender.com/api/v1/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Certificate of Completion",
       "event_name": "Full-Stack Python & FastAPI Engineering",
       "issuer_name": "Aerio Institute of Technology",
       "issue_date": "2026-10-07",
       "recipients": [
         {"name": "Alice Johnson", "email": "alice@example.com"},
         {"name": "Bob Smith", "email": "bob@example.com"},
         {"name": "Charlie Davis", "email": "charlie@example.com"}
       ]
     }'
```

---

### 2. Submit a Bulk Certificate Request via CSV Upload

**Endpoint**: `POST /api/v1/jobs/csv`  
**Form Data**: `file` (CSV file with `name` and `email` columns), `title`, `event_name`

```bash
curl -X POST "https://bulk-certificate-generator-rhgm.onrender.com/api/v1/jobs/csv" \
     -F "file=@participants.csv" \
     -F "title=Data Science Certificate" \
     -F "event_name=ML Bootcamp 2026"
```

---

### 3. Check Job Status & Progress

**Endpoint**: `GET /api/v1/jobs/{job_id}`  
Returns full status, counts, and individual recipient certificate statuses.

**Endpoint**: `GET /api/v1/jobs/{job_id}/progress`  
Returns concise progress percentage (`0.0%` to `100.0%`) and summary counts.

```bash
curl "https://bulk-certificate-generator-rhgm.onrender.com/api/v1/jobs/e4a67b2d-128c-4f9e-a813-0974bfa6c2e1/progress"
```

---

### 4. Retrieve Generated Certificates

#### Download Single PDF Certificate:
**Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`

```bash
curl -O "https://bulk-certificate-generator-rhgm.onrender.com/api/v1/certificates/f891b2c4-1111-2222-3333-444455556666/download"
```

#### Download All Certificates as ZIP:
**Endpoint**: `GET /api/v1/jobs/{job_id}/download-all`

```bash
curl -O "https://bulk-certificate-generator-rhgm.onrender.com/api/v1/jobs/e4a67b2d-128c-4f9e-a813-0974bfa6c2e1/download-all"
```

#### Verify Certificate Authenticity:
**Endpoint**: `GET /api/v1/certificates/verify/{certificate_code}`

```bash
curl "https://bulk-certificate-generator-rhgm.onrender.com/api/v1/certificates/verify/CERT-2026-0001-A1B2C3"
```

---

## 🛠️ Important Implementation & Design Decisions

1. **FastAPI BackgroundTasks vs Dedicated Task Queue**:
   - *Choice*: Used FastAPI's built-in `BackgroundTasks` for execution.
   - *Reasoning*: Keeps setup lightweight and dependency-free (no Redis/RabbitMQ server required to run locally or in test environments) while maintaining non-blocking HTTP 202 responses for clients.
2. **Database Isolation**:
   - Each job creation pre-generates `CertificateRecord` rows with unique verification codes (`CERT-2026-XXXX-XXXX`). The background worker opens a fresh database session, processing recipient items one by one and committing after each item.
3. **Partial Failure & Fault Isolation**:
   - If rendering a specific recipient's certificate fails (e.g., unexpected data anomaly or simulated failure trigger `__TRIGGER_FAIL__`), the error is captured and stored in `error_message`, marking that recipient as `FAILED`.
   - Other valid recipients proceed uninterrupted, updating the parent job status to `PARTIALLY_FAILED` instead of crashing the entire job.
4. **Dynamic Canvas Text Fitting**:
   - Implemented dynamic auto-scaling font size algorithms so extra-long recipient names (e.g. 80+ characters) or long event titles shrink gracefully without spilling over certificate borders.
5. **ZIP Bundling**:
   - Upon completion of a job, all successfully rendered PDF files are automatically archived into a `.zip` file stored under `generated_certificates/{job_id}/`.
