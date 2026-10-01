# ClinSaarthi AI (Clinical Knowledge Assistant)

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django 5.1](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript 6](https://img.shields.io/badge/TypeScript-6-3178c6.svg)](https://www.typescriptlang.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ed.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **MANDATORY MEDICAL DISCLAIMER**: ClinSaarthi AI is an educational clinical decision-support and knowledge-retrieval platform. It does NOT provide formal medical advice, definitive clinical diagnoses, or binding treatment prescriptions. All clinical decisions must be confirmed by licensed healthcare professionals. **Only synthetic, simulated patient records are used for testing and development.**

---

## 🌟 What is ClinSaarthi AI?
ClinSaarthi AI is a production-grade Healthcare RAG (Retrieval-Augmented Generation) & Agentic Q&A platform built for clinicians, residents, and medical students.

### Key Capabilities:
1. **Multi-Column Guideline Ingestion**: Parses multi-column medical PDF guidelines (e.g. AHA/ACC Atrial Fibrillation Guidelines), maintains reading order, extracts tables as Markdown, and computes spatial bounding boxes (`[x0, top, x1, bottom]`).
2. **Zero-Trust PII Masking & Reversible Diff**: De-identifies clinical notes locally with regex entity propagation (`[PATIENT_1]`, `[PHONE_1]`, `[AADHAAR_1]`), asserting zero raw identifiers leak into vector stores or LLMs. Original notes are accessible only to the uploader or administrators via an interactive side-by-side diff viewer.
3. **Dual-Source Hybrid RAG Retrieval**: Simultaneously retrieves evidence from published clinical guidelines and de-identified patient notes using Dense Embeddings (`BAAI/bge-m3`) + BM25 Lexical Search + Reciprocal Rank Fusion (RRF) + Cross-Encoder Reranker (`BAAI/bge-reranker-base`).
4. **LangGraph 8-Node Verification Agent**: Understands query intent → retrieves evidence → gates confidence → drafts grounded answers → extracts clinical claims → fact-checks against guidelines, NIH RxNorm, and openFDA → repairs hallucinated dosages → delivers verified guidance.
5. **Real-Time Streaming SSE Protocol**: Streams responses token-by-token with live pipeline progress badges (`understanding`, `retrieving`, `generating`, `verifying`), citation anchors `[1][2]`, and interactive bounding box highlights on a split-pane PDF canvas.
6. **Study Mode & Spaced Repetition (SRS)**: Synthesizes board-style multiple-choice quizzes and clinical flashcards with the SuperMemo SM-2 spaced repetition algorithm (`Again <1d`, `Hard 2d`, `Good 4d`, `Easy 7d`) and mastery analytics.
7. **PromptGuard Defense & Scoped Throttling**: Defends against prompt injection, jailbreaks, delimiter smuggling, and exfiltration with DRF scoped rate limiting (`ask: 30/min`, `notes: 20/min`, `quiz: 40/min`).
8. **100% Free Tools Only**: Zero paid API keys required. Powered by open-source Hugging Face models, local ChromaDB, PyMuPDF, spaCy, RxNorm, and openFDA.

---

## 🏗️ Architecture & Component Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      React 19 + TypeScript Frontend                         │
│  (SplitPane • PDFSourceCanvas • CitationChips • VerificationPanel • SRS)    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / Server-Sent Events (SSE)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Nginx Reverse Proxy (Port 80 / 3000)                    │
│   (Buffering Disabled for SSE • Static Asset Caching • Security Headers)   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               Django REST Framework (Thin Views / Port 8000)                │
│    (SimpleJWT • PromptGuard • ScopedRateThrottle • Multi-Tenant RBAC)       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Service & Agentic Domain Layer                        │
│   QAService • IngestionService • PIIMasker • VerificationService • Study    │
│   LangGraph: Understand ➔ Retrieve ➔ Gate ➔ Draft ➔ Extract ➔ Verify ➔ Repair│
└──────────────────────┬───────────────────────────────┬──────────────────────┘
                       │                               │
                       ▼                               ▼
       ┌───────────────────────────────┐ ┌────────────────────────────────────┐
       │ PostgreSQL 15 / SQLite3 DB    │ │ ChromaDB Vector Store (Disk Persist)│
       │ (Users, Conversations, Notes, │ │ (BGE-M3 Dense Embeddings + BM25    │
       │  Quizzes, Flashcards, SRS)    │ │  + Cross-Encoder Reranker)         │
       └───────────────────────────────┘ └────────────────────────────────────┘
```

---

## 🐳 Running with Docker Compose (Recommended)

Run the entire multi-container stack (PostgreSQL + Django ASGI + React/Nginx) with a single command:

```bash
# 1. Clone repository
git clone https://github.com/darshanthelucifer-png/Clinical-Knowledge-Assistant-.git
cd Clinical-Knowledge-Assistant-

# 2. Build and start containers
docker compose up --build
```

### Services & Port Mapping:
* **Frontend Web App**: `http://localhost:80` or `http://localhost:3000`
* **Backend REST API**: `http://localhost:8000/api/v1/`
* **Django Admin**: `http://localhost:8000/admin/`
* **PostgreSQL Database**: `localhost:5432` (database: `clinsaarthi`, user: `postgres`)

---

## 💻 Running Locally (Development Mode)

### Prerequisites:
* Python 3.11+
* Node.js v20+ / v22+ & npm
* Git

### 1. Backend Setup:
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv ../.venv
# On Windows:
..\.venv\Scripts\activate
# On Linux/macOS:
source ../.venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start backend dev server
python manage.py runserver 8000
```

### 2. Frontend Setup:
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🧪 Automated Test Suite (83 Tests Passing)

The project includes an exhaustive, production-grade test suite covering all architectural layers:

```bash
# From backend directory with virtual environment activated:
pytest -v
```

### Test Coverage Breakdown:
| Test Module | Coverage Area | Tests |
| :--- | :--- | :---: |
| `tests/test_auth.py` | JWT authentication, user registration, role RBAC (`clinician`, `student`, `admin`) | 7 |
| `tests/test_chunker.py` | 2-column layout reading order, table parsing, 400-token clinical chunking, bbox merging | 5 |
| `tests/test_evaluation.py` | 50-pair Golden QA benchmark, Hit-Rate@5, Faithfulness, Citation Precision | 4 |
| `tests/test_pii.py` | Regex PII masking, Aadhaar/phone detection, reversibility, note upload & diff | 8 |
| `tests/test_qa.py` | Grounded answers, inline citations `[1][2]`, confidence gating refusal, SSE streaming | 8 |
| `tests/test_retriever.py` | Dense vector store, BM25, RRF fusion, Cross-Encoder reranking | 6 |
| `tests/test_security.py` | PromptGuard jailbreak defense, scoped throttles (429), note isolation, security headers | 17 |
| `tests/test_study.py` | Multiple-choice quiz synthesis, SuperMemo SM-2 SRS flashcard scheduling, analytics | 7 |
| `tests/test_verifier.py` | LangGraph 8-node agent, claim extraction, RxNorm & openFDA API verification, repair loop | 18 |
| **Total** | **All Modules Passing Cleanly** | **83 / 83** |

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
