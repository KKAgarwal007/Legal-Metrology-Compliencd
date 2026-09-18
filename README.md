# AI-Powered Product Verification & Legal Metrology Compliance System

An enterprise-grade, explainable artificial intelligence system for automated detection, extraction, and statutory validation of mandatory declarations on packaged commodities under the **Legal Metrology Act, 2009** and the **Legal Metrology (Packaged Commodities) Rules, 2011**.

Powered by **PaddleOCR**, **RAG (Retrieval-Augmented Generation) Vector Knowledge Store**, and **Supabase Database**.

---

## 1. Methodology & Architecture

The system follows a 7-step inspection methodology:

```
[1. Input: Product Image]
          │
[2. Image Processing: Denoise, CLAHE Contrast, Orientation]
          │
[3. PaddleOCR: Text Extraction, Bounding Boxes, Confidence Scores]
          │
[4. Structured Information Extraction: Product Data, Units, Dates, ₹]
          │
[5. RAG Engine: Retrieve Applicable Legal Provisions from LM Act & Rules]
          │
[6. Compliance Engine: Check, Verify & Score against Statutory Thresholds]
          │
[7. Output: Dashboard, Interactive Dossier, Supabase DB, PDF Report]
```

### Three-Panel Inspection Dossier
1. **Evidence from OCR**: Cropped packaging image with highlighted green bounding box overlay, detected value, confidence percentage, and pixel coordinates `[x1, y1, x2, y2]`.
2. **Legal Basis (from RAG)**: Exact statutory requirements from the Legal Metrology (Packaged Commodities) Rules, 2011, rule/clause citations, and applicable penal provisions under Section 36 of the LM Act, 2009 with zero hallucination.
3. **Compliance Result Table**: Field-by-field verification (Product Name, Net Quantity, MRP, Manufacturer, Mfg Date, Best Before, Customer Care, Country of Origin, Unit Sale Price) with Pass/Review/Violation status badges.

---

## 2. Technology Stack

- **Computer Vision & OCR**: PaddleOCR (PP-OCRv4 with angle classification), OpenCV (CLAHE enhancement, EXIF transposition, barcode & QR code detection)
- **RAG Vector Knowledge Store**: Indexed statutory corpus of Legal Metrology Act, 2009 & Packaged Commodities Rules, 2011 with Gazette Amendments (2017, 2021, 2022)
- **Database**: Supabase PostgreSQL Cloud Database with dual-mode local SQLite fallback
- **Backend & Serving**: Python 3.12, Flask, Flask-Login, Flask-SQLAlchemy
- **Reporting**: ReportLab (vector PDF generation with zero external binary dependencies)
- **Design**: Modern enterprise CSS with responsive layouts, accessible typography, and interactive dossier panels

---

## 3. Quickstart & Installation

### 1. Activate Environment & Install Dependencies
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Supabase (Optional but Recommended)
Copy the example environment file:
```powershell
copy .env.example .env
```
Open `.env` and configure your Supabase project credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key
```

Run `supabase_schema.sql` in your [Supabase SQL Editor](https://app.supabase.com) to create the `products`, `scans`, `violations`, and `rag_legal_rules` tables with pre-seeded legal knowledge.

*Note: If Supabase credentials are not provided, the system runs automatically in local SQLite mode.*

### 3. Initialize Local Database
```powershell
python app.py initdb
```
Default credentials:
- **Admin**: `admin` / `ChangeMe123!`
- **Inspector**: `inspector1` / `ChangeMe123!`

### 4. Launch Application
```powershell
python app.py
```
Open your browser at `http://localhost:5000`.

---

## 4. Docker Deployment

The application includes a production-ready Dockerfile and `docker-compose.yml` pre-configured with PaddleOCR (PP-OCRv4), Tesseract OCR fallback, OpenCV headless runtime, and Gunicorn.

### Option A: Using Docker Compose (Recommended)

1. Ensure Docker Desktop is running.
2. Build and start the container with persistent storage:
```bash
docker compose up --build -d
```
3. View logs:
```bash
docker compose logs -f
```
4. Access the web interface at `http://localhost:5000` (Default credentials: `admin` / `ChangeMe123!`).
5. Stop the container:
```bash
docker compose down
```

### Option B: Using Docker CLI

1. **Build the image**:
```powershell
docker build -t lmc-compliance-app .
```

2. **Run the container**:

*In Windows PowerShell:*
```powershell
docker run -d `
  --name lmc_compliance_app `
  -p 5000:5000 `
  --env-file .env `
  -v "${PWD}/instance:/app/instance" `
  -v "${PWD}/uploads:/app/uploads" `
  -v "${PWD}/reports:/app/reports" `
  lmc-compliance-app
```

*Or single-line:*
```powershell
docker run -d --name lmc_compliance_app -p 5000:5000 --env-file .env -v "${PWD}/instance:/app/instance" -v "${PWD}/uploads:/app/uploads" -v "${PWD}/reports:/app/reports" lmc-compliance-app
```

*In Linux / macOS (Bash):*
```bash
docker run -d \
  --name lmc_compliance_app \
  -p 5000:5000 \
  --env-file .env \
  -v "${PWD}/instance:/app/instance" \
  -v "${PWD}/uploads:/app/uploads" \
  -v "${PWD}/reports:/app/reports" \
  lmc-compliance-app
```

---

## 5. RAG Statutory Knowledge API

Inspectors and developers can query the Legal Metrology RAG vector store directly:
```bash
GET /api/rag/query?q=penalty+for+selling+above+mrp
```
Returns structured JSON with matched legal clauses, requirements, official text, and penalty references.
