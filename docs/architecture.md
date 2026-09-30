# ClinSaarthi AI - Architectural Specification

## Overview
ClinSaarthi AI (Clinical Knowledge Assistant) is a production-grade Healthcare RAG & Agentic Q&A platform allowing clinicians and medical students to query multi-column medical guidelines and de-identified clinical notes with source-cited, verified answers.

```
                           +----------------------------------------+
                           |          React + Vite Frontend         |
                           |   (SourceViewer, VerificationPanel)    |
                           +-------------------+--------------------+
                                               |
                                     REST / SSE Streaming
                                               |
                                               v
+---------------------------------------------------------------------------------------+
|                                    Django REST Backend                                |
|                                                                                       |
|  +--------------------+     +---------------------+     +--------------------------+  |
|  |   DRF Thin Views   | --> |    Service Layer    | --> |    AI / Agent Layer      |  |
|  | (/ask, /notes,     |     | (QA, Ingestion, PII,|     | (LangGraph 8-Node Agent, |  |
|  |  /auth, /study)    |     |  Verification)      |     |  Retriever, Matcher)     |  |
|  +--------------------+     +----------+----------+     +------------+-------------+  |
+----------------------------------------|-----------------------------|----------------+
                                         |                             |
                       +-----------------+-----------------+           |
                       |                                   |           v
                       v                                   v    +---------------+
         +----------------------------+      +-------------+    | External APIs |
         |   PostgreSQL / SQLite      |      |   ChromaDB  |    |  (HuggingFace,|
         | (Users, Notes, Documents,  |      |   (Dense    |    |   RxNorm,     |
         |  Citations, Verifications) |      | Embeddings) |    |   openFDA)    |
         +----------------------------+      +-------------+    +---------------+
```

## Core Layers
1. **Presentation Layer**: Thin DRF views with async support for SSE token streaming.
2. **Service Layer**: Business logic modules (`qa_service`, `ingestion_service`, `pii_service`, `verification_service`, `study_service`).
3. **AI / Agent Layer**: LangGraph 8-node state machine (Understand -> Retrieve -> Confidence Gate -> Generate -> Extract -> Verify -> Repair -> Respond).
4. **Data Layer**: Relational models in PostgreSQL/SQLite + ChromaDB vector embeddings.
5. **External Medical References**: RxNorm (NIH) & openFDA (sanitized secondary validation, zero API key required).
