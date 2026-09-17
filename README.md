# Legal Metrology Compliance Inspection System

> **Smart India Hackathon 2026 — Problem Statement 26034**  
> *"Software System to check compliance of Packaged Commodities under Legal Metrology (Packaged Commodities) Rules, 2011 by scanning products, images and labels."*

---

## 1. Project Overview

The **Legal Metrology Compliance System** is an AI-assisted inspector-support platform designed to help Legal Metrology officers, state consumer affairs departments, and e-commerce compliance teams verify that packaged goods comply with the **Legal Metrology (Packaged Commodities) Rules, 2011** (as amended).

### What the System Does
1. **Scans & Ingests**: Accepts single or multi-panel images (front, back, sides) of packaged commodities.
2. **Preprocesses & OCRs**: Enhances package images and uses **PaddleOCR** (with Tesseract fallback) to extract all text regions with exact coordinates and recognition confidence scores.
3. **Extracts Declarations**: Uses structured LLM prompting to normalize detected text into mandatory declaration fields (MRP, Net Quantity, Manufacturer, Dates, Batch Number, Country of Origin, Consumer Care).
4. **Retrieves Legal Provisions**: Uses **PostgreSQL + pgvector** to retrieve exact sections and sub-rules from authoritative legal texts (LMR 2011).
5. **Checks Compliance Deterministically**: Evaluates extracted values against a hardcoded, transparent deterministic rule engine — producing **PASS**, **REVIEW**, or **VIOLATION**.
6. **Grounds Every Finding with Evidence**: Links every result directly to bounding box coordinates on the product image, the raw OCR text, and the governing legal rule.
7. **Generates Reports**: Produces tamper-evident PDF inspection reports with cryptographic hashes.

### Guiding Design Principle

$$\text{Evidence} \longrightarrow \text{Extraction} \longrightarrow \text{Rule} \longrightarrow \text{Deterministic Check} \longrightarrow \text{Explain}$$

> **Critical Note**: This is an **inspector-assistance tool**, NOT an automated replacement for designated legal authorities. The system does not claim 100% accuracy, does not claim zero hallucinations, and keeps the human inspector in the loop at every stage.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          INSPECTION PIPELINE                           │
└────────────────────────────────────────────────────────────────────────┘

   [Product Image(s)]  (Front / Back / Side / Top / Label)
           │
           ▼
   ┌───────────────────────┐
   │  IMAGE PREPROCESSING  │  Resize, Grayscale, CLAHE Contrast Enhancement,
   │       (OpenCV)        │  Denoising, Adaptive Thresholding, Perspective
   └───────────────────────┘
           │
           ▼
   ┌───────────────────────┐
   │       PADDLEOCR       │  Primary OCR engine: text detection + recognition
   │  (Tesseract fallback) │  Outputs: text, confidence (0.0–1.0), bounding boxes
   └───────────────────────┘
           │
           ▼
   ┌───────────────────────┐
   │   STRUCTURED FIELD    │  Gemini 2.0 Flash / LLM extracts canonical fields:
   │      EXTRACTION       │  MRP, Net Qty, Manufacturer, Pkd Date, Batch, etc.
   │   + NORMALIZATION     │  Strict JSON output, preserves raw source text
   └───────────────────────┘
           │
           ▼
   ┌───────────────────────┐
   │   RAG KNOWLEDGE BASE  │  Legal Metrology Act, 2009 & LMR 2011
   │  (pgvector: 384-dim)  │  Semantic retrieval of governing rules
   └───────────────────────┘
           │
           ▼
   ┌───────────────────────┐
   │  FIELD <-> RULE MAP   │  Ontological mapping from product fields
   │        LAYER          │  to applicable legal provisions
   └───────────────────────┘
           │
           ▼
   ┌───────────────────────┐
   │ DETERMINISTIC ENGINE  │  HARD RULES: required, regex, unit check, date validity
   │  (Non-LLM Decisions)  │  Outputs: PASS | REVIEW | VIOLATION
   └───────────────────────┘
           │
           ▼
   ┌───────────────────────┐
   │   EVIDENCE VIEWER     │  Interactive bounding box overlay + raw OCR source
   │    & PDF REPORT       │  + legal rule citations + SHA-256 tamper hash
   └───────────────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | React + TypeScript | 18.x | Dynamic SPA user interface |
| **Build Tool** | Vite | 6.x | Fast build & HMR development server |
| **Styling** | Tailwind CSS + shadcn/ui | 4.x / Radix | Government/enterprise UI design system |
| **Icons** | Lucide React | Latest | Clean, accessible iconography |
| **Backend** | FastAPI | 0.115.x | High-performance async Python REST API |
| **Data Validation** | Pydantic v2 | 2.9.x | Strict schema validation & serialization |
| **Database** | PostgreSQL | 16 | Relational store for inspections and audit trails |
| **Vector Search** | pgvector | 0.3.5 | Vector similarity search for legal RAG |
| **Primary OCR** | PaddleOCR | 2.8.x | Deep-learning OCR with angle classification |
| **Secondary OCR** | Tesseract | 5.x / pytesseract | Local fallback OCR engine |
| **Computer Vision** | OpenCV | 4.10.x | Image preprocessing, contrast, bounding boxes |
| **LLM Provider** | Google Gemini API | gemini-2.0-flash | Structured extraction & legal summarization |
| **Embeddings** | sentence-transformers | all-MiniLM-L6-v2 | 384-dimensional dense semantic vectors |
| **Document Parsing** | PyMuPDF (fitz) | 1.24.x | PDF extraction for legal document ingestion |
| **PDF Reporting** | WeasyPrint / Jinja2 | 62.x | Server-side PDF report rendering |
| **Containerization** | Docker + Docker Compose | 3.8 | Multi-container reproducible deployment |

---

## 4. Installation (Windows 11)

### Prerequisites
- **Python**: 3.11.x (64-bit) — [python.org](https://python.org)
- **Node.js**: 20.x LTS or higher — [nodejs.org](https://nodejs.org)
- **Git**: [git-scm.com](https://git-scm.com)
- **PostgreSQL 16** with **pgvector** OR **Docker Desktop**

### Clone Repository
```bash
git clone <repo-url> "D:/SIH Project"
cd "D:/SIH Project"
```

---

## 5. Environment Variables

Create `backend/.env` from the template:

```bash
copy backend\.env.example backend\.env
```

| Variable | Default Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/legal_metrology` | Async database connection string |
| `DATABASE_URL_SYNC` | `postgresql://postgres:postgres@localhost:5432/legal_metrology` | Sync connection string for migrations/scripts |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `API_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed frontend origins |
| `UPLOAD_DIR` | `./uploads` | Directory for uploaded package images |
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum allowed file upload size |
| `OCR_ENGINE` | `paddleocr` | Primary OCR engine (`paddleocr` or `tesseract`) |
| `OCR_LANG` | `en` | OCR language |
| `OCR_CONFIDENCE_HIGH` | `0.90` | Threshold for HIGH OCR confidence |
| `OCR_CONFIDENCE_MEDIUM` | `0.60` | Threshold for MEDIUM OCR confidence |
| `LLM_PROVIDER` | `gemini` | LLM provider (`gemini` or `mock`) |
| `GEMINI_API_KEY` | *(your key)* | Google AI Studio API key |
| `LLM_MODEL` | `gemini-2.0-flash` | LLM model for extraction |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace sentence transformer |
| `EMBEDDING_DIMENSION` | `384` | Vector dimension for pgvector |
| `SECRET_KEY` | *(random 32+ chars)* | JWT signing secret |
| `DEBUG` | `true` | Enable debug logging and Swagger UI |

---

## 6. Database Setup

### Option A: Using Docker (Recommended)
```bash
# Starts PostgreSQL 16 with pgvector and runs scripts/init_db.sql automatically
docker compose up -d postgres
```

### Option B: Local PostgreSQL on Windows
1. Install PostgreSQL 16 from [postgresql.org](https://www.postgresql.org/download/windows/).
2. Install pgvector for Windows:
   - Download the precompiled binary from the [pgvector GitHub releases](https://github.com/pgvector/pgvector/releases).
   - Copy `vector.dll` into `C:\Program Files\PostgreSQL\16\lib\`
   - Copy `vector.control` and `vector--*.sql` into `C:\Program Files\PostgreSQL\16\share\extension\`
3. Create the database and run the initialization script:
   ```bash
   psql -U postgres -c "CREATE DATABASE legal_metrology;"
   psql -U postgres -d legal_metrology -f scripts/init_db.sql
   ```

---

## 7. PaddleOCR Installation (Windows)

PaddleOCR requires PaddlePaddle. For Windows 64-bit with CPU:

```bash
# Inside your Python virtual environment:
python -m pip install paddlepaddle==2.6.2 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
python -m pip install paddleocr==2.8.1
```

> **Windows Known Issues & Fixes**:
> - **Visual C++ Redistributable**: Ensure the [MSVC v143 redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) is installed.
> - **Long Path Support**: Enable Windows long paths in the registry: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`.
> - **Model Download**: On first run, PaddleOCR automatically downloads detection/recognition models (~15MB) to `~/.paddleocr/`. Ensure internet access on first launch.

---

## 8. Legal Document Ingestion

The system includes pre-configured Legal Metrology rules, but you can ingest raw official PDFs into the RAG vector store:

```bash
# Ingest an official gazette notification or rules document:
python scripts/ingest_regulations.py \
    --file data/regulations/Legal_Metrology_Packaged_Commodities_Rules_2011.pdf \
    --name "Legal Metrology (Packaged Commodities) Rules, 2011" \
    --version "2011"

# Generate pgvector embeddings for any pending chunks:
python scripts/create_embeddings.py
```

---

## 9. Running Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server with hot-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be accessible at:
- **Interactive Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/api/health`

---

## 10. Running Frontend

```bash
cd frontend

# Install npm dependencies
npm install

# Start development server
npm run dev
```

Application will be accessible at: `http://localhost:5173`

---

## 11. Running Demo (Seed Data)

To demonstrate the system to judges without waiting for image uploads or live OCR runs, use the seed scripts:

```bash
# Step 1: Seed the official Legal Metrology compliance rules
python scripts/seed_compliance_rules.py

# Step 2: Seed demo inspections (PASS, REVIEW, and VIOLATION examples)
python scripts/seed_demo_data.py
```

Demo inspector login credentials:
- **Email**: `inspector@example.com`
- **Password**: `password123`

The demo dataset contains:
1. **PASS Case**: *Royal Feast Premium Basmati Rice 1kg* — All Rule 6 declarations present, clear, and compliant.
2. **REVIEW Case**: *Naturale Herbal Essence Hair Cleanser 200ml* — Batch number partially obscured by package crimp (OCR conf 0.51); requires physical inspector review.
3. **VIOLATION Case**: *Alpine Pure Swiss Dark Chocolate 100g (Imported)* — No MRP declared anywhere; imported commodity lacks Country of Origin declaration (violations of Rule 6(1)(e) and Rule 6(1)(f)).

---

## 12. API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/inspections` | Create a new inspection record |
| `GET` | `/api/inspections` | List inspections with pagination & filtering |
| `GET` | `/api/inspections/{id}` | Get full details of a specific inspection |
| `POST` | `/api/inspections/{id}/images` | Upload multi-panel product images |
| `POST` | `/api/ocr/{inspection_id}` | Execute OCR on uploaded images |
| `POST` | `/api/extract/{inspection_id}` | Extract structured product declarations |
| `POST` | `/api/compliance/{inspection_id}`| Run deterministic compliance engine |
| `POST` | `/api/process/{inspection_id}` | Run complete one-click pipeline |
| `GET` | `/api/inspections/{id}/ocr` | Get raw OCR results with bounding boxes |
| `GET` | `/api/inspections/{id}/fields` | Get extracted product declarations |
| `GET` | `/api/inspections/{id}/compliance`| Get rule evaluation results |
| `GET` | `/api/inspections/{id}/evidence` | Get grounded image evidence records |
| `GET` | `/api/inspections/{id}/report` | Get/generate compliance report |
| `PATCH`| `/api/fields/{field_id}` | Manually correct an extracted declaration |
| `POST` | `/api/rag/search` | Semantic search over legal provisions |
| `POST` | `/api/regulations/ingest` | Upload and process a legal document PDF |
| `GET` | `/api/health` | Service health status |

---

## 13. Database Schema

The system uses 13 normalized tables in PostgreSQL:

- **`users`**: Inspectors and administrators with role-based access.
- **`inspections`**: Inspection sessions containing status, category, overall verdict, and timestamps.
- **`inspection_images`**: Uploaded product panel images (original, preprocessed, OCR visualization).
- **`ocr_results`**: Preserved raw OCR tokens with bounding boxes `[x1, y1, x2, y2]`, confidence scores, and correction audit trails.
- **`products`**: Extracted product entity linked 1:1 with inspection.
- **`product_fields`**: Granular extracted declarations with normalization, raw values, confidence, and bounding box coordinates.
- **`regulations`**: Official legal texts metadata (title, version, gazette date).
- **`regulation_chunks`**: Chunked legal text with 384-dimensional `pgvector` embeddings for semantic search.
- **`compliance_rules`**: Structured Legal Metrology rules with deterministic operators.
- **`field_rule_mappings`**: Mapping linking field ontology to governing rule records.
- **`compliance_results`**: Rule evaluation outputs (**PASS**, **REVIEW**, **VIOLATION**) with deterministic rationales.
- **`evidence`**: Grounded links between compliance results, image regions, and legal text chunks.
- **`reports`**: Generated PDF inspection reports with SHA-256 tamper-evident integrity hashes.

---

## 14. RAG Architecture

The Legal Knowledge Base is grounded **exclusively in authoritative government publications**:
- *The Legal Metrology Act, 2009 (No. 1 of 2010)*
- *Legal Metrology (Packaged Commodities) Rules, 2011* (GSR 202(E))
- *Subsequent official amendments (2017, 2021, 2022, 2024)*

```
[Official Gazette PDF]
         │
         ▼
[PyMuPDF Page Extraction]
         │
         ▼
[Rule-Aware Semantic Chunking]  (Splits along Rule 6(1)(a), Rule 6(1)(b), etc.)
         │
         ▼
[Metadata Tagging]               (Document, Rule Number, Page, Effective Date)
         │
         ▼
[all-MiniLM-L6-v2 Embeddings]   (384-dimensional dense vectors)
         │
         ▼
[PostgreSQL + pgvector]         (Stored with IVFFlat cosine similarity index)
         │
         ▼
[Cosine Similarity Search]       (Triggered during field-to-rule mapping)
```

> **Strict Rule**: The RAG pipeline retrieves legal context to inform and cite; **it does not make the final compliance decision**. Decisions are made by the deterministic engine.

---

## 15. Compliance Engine

The deterministic engine evaluates extracted declarations against formal rule definitions. It supports:

- `required`: Field must be detected with confidence $\ge 0.60$.
- `not_empty`: Field string must have length $> 0$.
- `regex`: Format validation (e.g., MM/YYYY date formats, phone number structure).
- `date_valid`: Checks that declared dates are chronologically plausible.
- `unit_check`: Verifies Net Quantity uses approved SI units (g, kg, ml, L, m, cm).
- `conditional`: Rules activated only when specific conditions are met (e.g., Country of Origin required *if* imported).

### Three-Tier Decision Logic

```
   ┌─────────────────────────────────────────────────────────────────┐
   │ PASS: Evidence detected with sufficient confidence              │
   │       AND all deterministic rule conditions satisfied.           │
   ├─────────────────────────────────────────────────────────────────┤
   │ REVIEW: Required info is missing, OCR confidence < 0.60,       │
   │         text ambiguous, or situation requires legal discretion. │
   ├─────────────────────────────────────────────────────────────────┤
   │ VIOLATION: Positive evidence demonstrates a clear violation of  │
   │            a deterministic requirement (e.g. invalid units).     │
   └─────────────────────────────────────────────────────────────────┘
```

---

## 16. Testing

```bash
cd backend

# Run all automated tests
pytest tests/ -v

# Run specific compliance engine tests
pytest tests/test_compliance_engine.py -v

# Run with test coverage report
pytest --cov=app tests/
```

Test scenarios covered:
- Standard compliant product packaging.
- Missing MRP declaration handling.
- Low OCR confidence threshold triggering REVIEW status.
- Imported products without Country of Origin triggering VIOLATION.
- Non-standard Net Quantity units (e.g., using "ounces" instead of grams).
- Manual correction override audit trail integrity.

---

## 17. Known Limitations & Responsible AI Disclaimer

1. **Inspector-Assistance System**: This software is designed exclusively as an operational aid for trained Legal Metrology inspectors. **Final legal determinations and issuance of notices under Section 39 of the Legal Metrology Act, 2009 rest solely with competent statutory authorities.**
2. **OCR Real-World Variability**: Extremely reflective packaging (foil pouches), curved cylindrical surfaces (cans), and damaged labels may reduce OCR confidence. In such cases, the system safely falls back to `REVIEW_REQUIRED` rather than guessing.
3. **No Hallucinated Rules**: The system uses a closed-world assumption: it only cites rules present in its database/RAG repository. It will never invent legal citations.
4. **Offline Capability**: The core deterministic engine, OCR pipeline, and PostgreSQL database run entirely on-premises without requiring external cloud connectivity, ensuring data sovereignty for government deployments.
