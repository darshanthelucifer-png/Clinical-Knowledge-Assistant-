# ClinSaarthi AI — 2-Minute Interview Walkthrough & Presentation Guide

> **Target Role**: Full-Stack AI Engineer / Applied AI Engineer / Backend AI Engineer  
> **Target Audience**: Technical Lead, Staff AI Engineer, or Engineering Hiring Manager  
> **Delivery Cadence**: ~140 words/minute, conversational yet authoritative, emphasizing engineering trade-offs, clinical safety guardrails, and zero-trust data privacy.

---

## ⏱️ The 2-Minute Spoken Walkthrough Script

### **[0:00 – 0:30] The Hook & Clinical Problem**
*(Delivery: Confident, engaging, establishing domain context)*

> "Hi, I’m excited to share **ClinSaarthi AI**, a production-grade Healthcare RAG and Agentic Decision-Support platform I built for clinicians and medical students.
> 
> In healthcare, practitioners spend hours cross-referencing dense 50-page clinical guidelines with complex EHR notes. But generic LLMs pose two critical hazards: **they hallucinate lethal drug dosages** without source attribution, and **they risk HIPAA violations** by transmitting raw patient Protected Health Information (PHI) to third-party endpoints.
> 
> To solve this, I designed ClinSaarthi AI on a strict constraint: **100% free, open-source tools with zero paid API keys**, combining deterministic zero-trust PII masking, dual-source hybrid retrieval, and an 8-node LangGraph verification agent."

---

### **[0:30 – 1:00] Ingestion & Zero-Trust Privacy Architecture**
*(Delivery: Technical precision, demonstrating systems thinking)*

> "On the data ingestion side, medical manuals use complex multi-column layouts. Using PyMuPDF, I engineered a column-aware layout extractor that calculates bounding boxes (`[x0, top, x1, bottom]`), preserves sequential reading order across columns, and parses dosage tables into structured Markdown.
> 
> For clinical patient notes, I built a zero-trust **PII Masker**. Before any note hits our vector store or an LLM, a multi-category regex pipeline with referential consistency replaces names, Aadhaar numbers, phone numbers, and MRNs with pseudonyms like `[PATIENT_1]` and `[PHONE_1]`. 
> 
> An isolated database mapping table allows only the authorized clinician to view a side-by-side unmasking diff, while asserting zero raw PHI leaks into embeddings or model prompts."

---

### **[1:00 – 1:30] Dual-Source Hybrid RAG & The LangGraph Agent**
*(Delivery: Highlighting agentic AI & safety guardrails)*

> "For retrieval, queries run through a dual-source hybrid pipeline: dense embeddings using `BAAI/bge-m3` in ChromaDB combined with BM25 lexical search, fused via Reciprocal Rank Fusion (RRF) and reranked using a BGE Cross-Encoder.
> 
> To prevent hallucinations on out-of-domain queries, I engineered a **Confidence Gate** at 0.50 score threshold with stop-word filtering. If evidence is lacking, the system refuses to answer rather than guessing.
> 
> When queries pass the gate, our **LangGraph 8-node agent** takes over: it drafts an answer with inline citation anchors `[1][2]`, extracts clinical claims using medical NLP, and cross-checks every drug, dosage, and frequency against public NIH RxNorm and openFDA APIs. If a dosage conflicts with the guideline, an iterative repair loop rewrites the claim before sending the response."

---

### **[1:30 – 2:00] User Experience, Study Mode & Production Engineering**
*(Delivery: Closing with strong product polish and DevOps maturity)*

> "On the frontend, built with React 19, TypeScript, and Vite, answers stream in real-time via Server-Sent Events (SSE). Clinicians can click any inline citation chip, and the split-pane PDF canvas instantly scrolls to the exact page and highlights the source bounding box.
> 
> For residents, I also built a **Study Mode** that synthesizes multiple-choice quizzes and clinical flashcards powered by the SuperMemo SM-2 Spaced Repetition algorithm.
> 
> From an engineering standpoint, the entire system is hardened with PromptGuard jailbreak defenses, scoped rate limiting, 83 automated pytest unit/integration tests, and multi-stage Docker Compose orchestration with Nginx configured for unbuffered SSE streaming.
> 
> I’d love to walk you through a quick live demo or dive into any of the architectural components!"

---

## ⚡ 30-Second Elevator Pitch (Recruiter & Quick Intro Version)

> "I built **ClinSaarthi AI**, an enterprise-grade clinical decision-support and RAG platform that allows doctors to query multi-column medical guidelines alongside de-identified patient notes with 100% verified, source-cited answers. 
> 
> It features zero-trust PII masking, a hybrid Dense + BM25 + Cross-Encoder retrieval pipeline with strict confidence gating, and an 8-node LangGraph agent that verifies drug dosages against NIH RxNorm and openFDA APIs. 
> 
> Built with Django 5, React 19, and ChromaDB, the entire platform runs on 100% free open-source tools with zero paid API keys, backed by 83 automated tests and Docker containerization."

---

## 🎯 5 "WOW" Moments to Showcase During a Live Demo

| # | Demo Action | What the Interviewer Sees | Architectural Insight to Mention |
| :--- | :--- | :--- | :--- |
| **1** | Ask: *"What is the first-line anticoagulant for non-valvular AF?"* | Live SSE token streaming with status badges (`understanding`, `retrieving`, `generating`, `verifying`), inline citations `[1]`, and a verified dosage badge. | *"Notice how the SSE protocol streams tokens while the verifier runs asynchronously in the background."* |
| **2** | Click Citation Chip `[1]` in chat answer | The right-hand PDF canvas instantly navigates to Page 1, draws a semi-transparent amber highlight rectangle over the exact source paragraph. | *"Coordinates are extracted during PyMuPDF ingestion and merged across sentence envelopes without rendering heavy images."* |
| **3** | Ask an irrelevant question: *"What is quantum entanglement?"* | Strict refusal: *"I'm not sure — this information is not found in the provided clinical guidelines."* | *"Our cross-encoder reranker uses stop-word filtering to prevent false lexical matches, dropping out-of-domain scores below the 0.50 threshold."* |
| **4** | Upload a clinical note with patient names and phone numbers | Instant side-by-side diff highlighting red redactions and green replacements, with a badge showing *"3 PII Entities Redacted"*. | *"Entity propagation guarantees referential consistency (`[PATIENT_1]`) while the isolated mapping ensures raw PHI never touches vector storage."* |
| **5** | Flip a flashcard in Study Mode and rate *"Good (4d)"* | 3D perspective flip card showing clinical vignette and guideline recommendation, with next review interval scheduled by SuperMemo SM-2. | *"The SM-2 algorithm calculates repetitions, interval days, and ease factor directly in the service layer."* |

---

## 💡 Top 5 High-Impact Technical Talking Points

1. **Why Hybrid Search + Cross-Encoder?**
   * *Dense retrieval* (`bge-m3`) captures medical semantic meaning (e.g., mapping "irregular heartbeat" to "atrial fibrillation").
   * *Sparse lexical search* (`BM25`) ensures exact keyword precision for complex pharmaceutical brand names and numerical dosages (e.g., "5 mg bid").
   * *Reciprocal Rank Fusion (RRF)* merges both candidate lists without score scale mismatches, and the *BGE Cross-Encoder* performs full joint query-document cross-attention on the top candidates.

2. **How Was Stop-Word Cross-Encoder Drift Solved?**
   * Unfiltered queries allowed general words ("what", "is", "the") to match background guideline paragraphs with artificial ~0.50 scores.
   * Stripping English stop words prior to cross-encoder evaluation dropped out-of-domain queries to `0.175`, cleanly triggering the confidence gate refusal, while clinical queries score `> 0.65`.

3. **Why Dual-Source RAG (Guidelines + Notes)?**
   * Real clinical workflows require comparing patient history against medical literature.
   * Chunks are tagged with `document_id` and document type. Queries can retrieve from both simultaneously, enabling comparative questions like: *"Is this patient's current amiodarone regimen consistent with AHA AFib guidelines?"*

4. **Why LangGraph for Agentic Verification?**
   * Linear chains fail silently if an LLM hallucinates a dosage.
   * An explicit state graph (`StateGraph`) with cyclic edges allows an iterative **Repair Loop**: if an extracted claim is marked `CONFLICT` against RxNorm or guideline chunks, the repair node builds a corrective directive and regenerates the answer up to 2 times before falling back to a safety warning banner.

5. **Security & Production Hardening**:
   * Scoped rate throttling (`ask: 30/min`, `notes: 20/min`, `quiz: 40/min`) protects compute-heavy pipelines.
   * `PromptGuard` intercepts adversarial prompt injection and delimiter attacks using precompiled regex threat filters before input reaches the vector store or LLM.
   * Multi-stage Docker setup with Nginx proxy buffering disabled for unbuffered SSE streaming.
