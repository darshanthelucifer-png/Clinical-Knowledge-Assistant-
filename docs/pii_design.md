# ClinSaarthi AI - Zero-Trust PII / PHI De-identification Design

## Privacy Guarantee
Under no circumstances does raw, unmasked Protected Health Information (PHI) reach:
- Large Language Models (LLM prompts)
- Dense Embedding models
- Vector store indexes (ChromaDB / FAISS)
- System application logs

## Redaction Architecture
1. **Pre-Ingestion Redaction**: When a clinical note is submitted, `PIIMasker.mask()` executes synchronously before saving to the database.
2. **Reversible Placeholders**: Identifiers are replaced by deterministic, tagged placeholders:
   - Patient Name -> `[PATIENT_1]`
   - Phone Numbers -> `[PHONE_1]`
   - Email Addresses -> `[EMAIL_1]`
   - Medical Record Numbers -> `[MRN_1]`
   - Dates of Birth -> `[DOB_1]`
   - SSN / National IDs -> `[SSN_1]`, `[AADHAAR_1]`
3. **Restricted Storage**: The mapping from placeholder back to raw value is stored in `PIIMapping`, an isolated, access-controlled table.
4. **Access Control**: Only the original authenticated uploader (or authorized compliance administrator) can request the `/notes/<id>/diff/` endpoint.
