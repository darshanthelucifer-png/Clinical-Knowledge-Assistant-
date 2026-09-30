# ClinSaarthi AI (Clinical Knowledge Assistant)

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django 5.0](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **IMPORTANT DISCLAIMER**: ClinSaarthi AI is an educational clinical decision-support tool. It does NOT provide clinical medical advice. All recommendations must be verified by licensed healthcare providers. **Only synthetic, simulated data is used for testing and development.**

---

## 🌟 What is ClinSaarthi AI?
ClinSaarthi AI is an enterprise-grade Healthcare RAG (Retrieval-Augmented Generation) & Agentic Q&A platform built for clinicians and medical students. It allows users to:
1. **Query Multi-Column Clinical Guidelines**: Query medical manuals and guidelines with citations pointing to the exact book, page, and highlighted coordinates.
2. **De-Identify Clinical Notes**: Upload clinical notes with zero-trust PII masking (names, phone numbers, emails, MRNs, DOBs, SSNs) before any vector indexing or LLM inference.
3. **Fact-Verify Answers**: Run an agentic audit on every drug, dosage, unit, and frequency against retrieved source text (categorized as `VERIFIED`, `UNSUPPORTED`, or `CONFLICT`).
4. **Study & Quiz Mode**: Generate multiple-choice quizzes and flashcards grounded directly in medical guidelines.
5. **100% Free Tools Only**: Zero paid APIs. Powered by Hugging Face open-source models, ChromaDB, spaCy/scispaCy, RxNorm, and openFDA.

---

## 🏗️ Architecture & Tech Stack

```
React (Vite + TS + Tailwind)
          ↓ (REST / SSE Streaming)
Django REST Framework (Thin Views)
          ↓
Service Layer (qa_service, ingestion_service, pii_service, verification_service)
          ↓
LangGraph 8-Node Agent (Understand → Retrieve → Gate → Generate → Extract → Verify → Repair → Respond)
          ↓
PostgreSQL / SQLite + ChromaDB Vector Store + Free Hugging Face Models
```

- **Backend**: Python 3.11, Django 5.0, Django REST Framework, SimpleJWT, Uvicorn (ASGI)
- **Vector DB**: ChromaDB (locally persisted) / FAISS (swappable behind `BaseVectorStore`)
- **LLMs & Embeddings**: Hugging Face Inference (`Qwen/Qwen2.5-7B-Instruct`, `BAAI/bge-m3`, `BAAI/bge-reranker-base`)
- **Medical NLP**: spaCy / scispaCy for entity extraction, DeBERTa-v3 for NLI entailment
- **Public Reference APIs**: RxNorm (NIH/NLM) and openFDA (both free, zero keys required)

---

## 🚀 Phase 1 Setup & Execution

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/darshanthelucifer-png/Clinical-Knowledge-Assistant-.git
cd Clinical-Knowledge-Assistant-

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Database Migrations
```bash
cd backend
python manage.py makemigrations accounts documents notes qa study evaluation
python manage.py migrate
```

### 4. Running the Test Suite
```bash
# From the backend directory
pytest tests/test_auth.py tests/test_pii.py -v
```

### 5. Running the Backend Server
```bash
python manage.py runserver
```
Visit the health check endpoint at: `http://127.0.0.1:8000/api/health/`
