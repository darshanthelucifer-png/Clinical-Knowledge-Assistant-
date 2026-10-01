"""
Seed demo data for ClinSaarthi AI local testing
"""
import os
import sys
from pathlib import Path
import django

# Setup Django environment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User
from apps.documents.models import Document
from apps.notes.models import ClinicalNote, PIIMapping
from services.ingestion_service import IngestionService
from services.pii_service import PIIMasker
from services.evaluation_service import EvaluationService
from services.study_service import StudyService

def seed():
    print("1. Creating demo clinician user...")
    user, created = User.objects.get_or_create(
        username="demo_clinician",
        defaults={
            "email": "clinician@clinsaarthi.ai",
            "role": User.Role.CLINICIAN,
            "department": "Cardiology",
            "first_name": "Sarah",
            "last_name": "Patel"
        }
    )
    if created:
        user.set_password("Password123!")
        user.save()
        print("   Created user: demo_clinician (Password: Password123!)")
    else:
        print("   User demo_clinician already exists.")

    print("\n2. Ingesting clinical guideline PDF...")
    pdf_path = Path(__file__).resolve().parent.parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    if pdf_path.exists():
        doc, doc_created = Document.objects.get_or_create(
            title="AHA/ACC/HRS Guideline for the Management of Atrial Fibrillation",
            defaults={
                "file": str(pdf_path),
                "uploaded_by": user
            }
        )
        if doc_created or doc.chunks.count() == 0:
            print("   Processing chunks and vectors for guideline...")
            IngestionService.process_document(str(doc.id))
            doc.refresh_from_db()
            print(f"   Ingested {doc.chunks.count()} guideline chunks with bounding boxes!")
        else:
            print(f"   Guideline already ingested ({doc.chunks.count()} chunks).")
    else:
        print(f"   Warning: PDF not found at {pdf_path}")
        doc = None

    print("\n3. Creating sample de-identified clinical note...")
    note_title = "Admission Note - Atrial Fibrillation with RVR"
    if not ClinicalNote.objects.filter(title=note_title).exists():
        raw_content = (
            "Patient: Rajesh Sharma, Age: 64, Male, MRN: MRN-8849201.\n"
            "Phone: +91 9876543210, Aadhaar: 9876 5432 1098.\n"
            "Date of Admission: 2026-09-28.\n\n"
            "Chief Complaint: Palpitations and acute shortness of breath for 12 hours.\n\n"
            "History of Present Illness: Patient presents with acute onset irregular tachycardia. "
            "12-lead ECG demonstrates Atrial Fibrillation with rapid ventricular response (heart rate 142 bpm). "
            "Echocardiogram reveals preserved left ventricular ejection fraction (LVEF 55%), mild left atrial dilation (4.2 cm), "
            "and normal renal function (eGFR 78 mL/min/1.73m2, Serum Creatinine 1.0 mg/dL). "
            "CHA2DS2-VASc score calculated as 2 (Hypertension, Age 64).\n\n"
            "Current Medications: Amlodipine 5mg daily, Metoprolol Tartrate 25mg bid.\n\n"
            "Clinical Plan: Initiate rate control with Metoprolol Succinate 50mg daily. "
            "Initiate stroke prophylaxis with Apixaban 5mg orally twice daily. "
            "Patient counseled on adherence and bleeding precautions. Follow-up in Cardiology clinic in 2 weeks."
        )
        mask_res = PIIMasker.mask(raw_content)
        note = ClinicalNote.objects.create(
            title=note_title,
            masked_content=mask_res.masked_text,
            pii_entity_count=len(mask_res.mapping),
            uploader=user,
            department="Cardiology"
        )
        PIIMapping.objects.create(
            note=note,
            mapping_data=mask_res.mapping,
            categories_detected=mask_res.categories_detected
        )
        print(f"   Created note: {note.title} (Redacted {len(mask_res.mapping)} PII entities)")
    else:
        print("   Sample note already exists.")

    print("\n4. Seeding Golden QA benchmark dataset...")
    count = EvaluationService.seed_golden_qa_table()
    print(f"   Seeded {count} Golden QA benchmark pairs.")

    print("\n5. Generating demo Quiz & Flashcard set...")
    if doc:
        quiz = StudyService.generate_quiz(
            user=user,
            document_id=str(doc.id),
            topic="Atrial Fibrillation Anticoagulation",
            count=3
        )
        print(f"   Generated demo quiz: '{quiz.title}' with {quiz.questions.count()} board-style MCQs.")

        fset = StudyService.generate_flashcards(
            user=user,
            document_id=str(doc.id),
            topic="Anticoagulation Dosages & Mechanisms",
            count=3
        )
        print(f"   Generated demo flashcards deck: '{fset.title}' with {fset.cards.count()} cards.")

    print("\n Seed completed successfully!")

if __name__ == "__main__":
    seed()
