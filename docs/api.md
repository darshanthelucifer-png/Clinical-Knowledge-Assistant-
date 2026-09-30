# ClinSaarthi AI - API Reference Specification

## Base URL
`/api/v1/`

## Endpoints

### 1. Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/register/` - Create new clinician or student account.
- `POST /api/v1/auth/login/` - Authenticate credentials and receive access/refresh JWT tokens with custom role claims.
- `POST /api/v1/auth/refresh/` - Refresh expired access token.
- `GET /api/v1/auth/me/` - Retrieve authenticated user profile and medical credentials.

### 2. Documents & Guidelines (`/api/v1/documents/`)
- `GET /api/v1/documents/` - List ingested guidelines.
- `POST /api/v1/documents/` - Upload guideline PDF for ingestion.
- `GET /api/v1/documents/<id>/` - Document metadata.
- `GET /api/v1/documents/<id>/chunks/` - Column-parsed chunks with bounding boxes.

### 3. Clinical Notes (`/api/v1/notes/`)
- `GET /api/v1/notes/` - List user's de-identified notes.
- `POST /api/v1/notes/upload/` - Upload note; masks PII immediately before storage.
- `GET /api/v1/notes/<id>/diff/` - Side-by-side original vs masked view (restricted to uploader).

### 4. Question Answering (`/api/v1/qa/`)
- `GET /api/v1/qa/conversations/` - List conversation threads.
- `POST /api/v1/qa/ask/` - Ask clinical question (SSE stream with citations & verifications).

### 5. Study Mode (`/api/v1/study/`)
- `GET /api/v1/study/quizzes/` - List guideline-grounded quizzes.
- `GET /api/v1/study/flashcards/` - List guideline flashcards.

### 6. Evaluation Dashboard (`/api/v1/evaluation/`)
- `GET /api/v1/evaluation/runs/` - Benchmark results (hit-rate@5, faithfulness, citation accuracy).
