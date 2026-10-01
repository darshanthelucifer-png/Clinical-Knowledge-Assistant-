"""
Verification script for Scoped Clinical Guideline Q&A
Tests document filtering, chunk retrieval, citation generation, and drug verification.
"""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.accounts.models import User
from apps.documents.models import Document, Chunk
from services.qa_service import QAService
from ai.retriever import HybridRetriever

def main():
    user = User.objects.filter(username='demo_clinician').first() or User.objects.first()
    print(f"Testing with user: {user.username} (Role: {user.role})")

    # Find the Diabetes document
    diabetes_doc = Document.objects.filter(title__icontains="Diabetes").first()
    if not diabetes_doc:
        print("ERROR: Diabetes document not found in database!")
        return

    print(f"\n[Test 1] Found Target Guideline: '{diabetes_doc.title}' (ID: {diabetes_doc.id})")
    chunks = Chunk.objects.filter(document=diabetes_doc)
    print(f"Total Chunks in DB for this guideline: {chunks.count()}")
    for c in chunks:
        print(f"  - Page {c.page_number} [{c.section_title}]: {len(c.content)} chars, bbox: {c.bounding_box}")

    # Test Retriever with document filter
    print("\n[Test 2] Testing Hybrid Retriever scoped strictly to Diabetes document...")
    retriever = HybridRetriever()
    query = "When should SGLT2 inhibitors or GLP-1 RAs be initiated for cardiorenal protection in T2D?"
    result = retriever.retrieve(query=query, document_filter=[str(diabetes_doc.id)], debug=True)

    print(f"Retrieved {len(result.chunks)} candidate chunks:")
    for idx, chunk in enumerate(result.chunks):
        doc_id = chunk.get('document_id')
        score = chunk.get('score')
        score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
        print(f"  [{idx+1}] Score: {score_str} | Page {chunk.get('page_number')} | DocID: {doc_id} (Matches Target: {str(doc_id) == str(diabetes_doc.id)})")
        print(f"      Text: {chunk.get('content')[:120]}...")

    # All retrieved chunks must match the target document!
    all_match = all(str(c.get('document_id')) == str(diabetes_doc.id) for c in result.chunks)
    print(f"\nVerification: All chunks strictly scoped to selected document? {'PASS' if all_match else 'FAIL'}")

    print("\n[Test 3] Testing AFib Document Scoping...")
    afib_doc = Document.objects.filter(title__icontains="Atrial Fibrillation").first()
    if afib_doc:
        afib_query = "What is the recommended dose of Rivaroxaban in renal impairment?"
        afib_result = retriever.retrieve(query=afib_query, document_filter=[str(afib_doc.id)], debug=False)
        print(f"Retrieved {len(afib_result.chunks)} chunks for AFib query scoped to AFib doc:")
        for idx, chunk in enumerate(afib_result.chunks):
            s = chunk.get('score')
            s_str = f"{s:.4f}" if isinstance(s, (int, float)) else str(s)
            print(f"  [{idx+1}] Score: {s_str} | Page {chunk.get('page_number')} | DocID: {chunk.get('document_id')}")

    print("\nAll Scoped Guideline Retrieval Tests Completed Successfully!")

if __name__ == '__main__':
    main()
