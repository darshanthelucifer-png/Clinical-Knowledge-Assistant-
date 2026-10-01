"""
================================================================================
ClinSaarthi AI - Intent Routing, Grounded Answering & Verification Test Suite
================================================================================
Validates:
1. "hello" returns conversational greeting with NO citations, NO verification table,
   and NO confidence score.
2. "who won the world cup" returns off-topic reply explaining clinical scope with
   NO citations and NO verification table.
3. The Rivaroxaban question returns verification rows containing ONLY Rivaroxaban
   (no competing drug rows such as Apixaban or Dabigatran).
4. Two different medical questions return distinctly different answers.
5. Confidence gate uses the real rerank score and provides rephrase suggestions
   when evidence is not found in the documents.
6. REST API /api/v1/qa/ask/ accepts HTTP_ACCEPT="text/event-stream" with 200 OK.
================================================================================
"""
import pytest
import json
from pathlib import Path
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document, Chunk
from services.qa_service import QAService
from ai.intent_router import IntentRouter


@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="dr_tester",
        email="tester@hospital.org",
        password="TestPassword123!",
        role=User.Role.CLINICIAN,
        department="Internal Medicine"
    )


@pytest.fixture
def afib_and_copd_guidelines(clinician_user, db):
    """Seed test guideline chunks for Atrial Fibrillation and COPD."""
    doc_afib = Document.objects.create(
        title="2026 AHA/ACC/HRS Guideline for Atrial Fibrillation",
        file="guidelines/afib.pdf",
        uploaded_by=clinician_user
    )
    c1 = Chunk.objects.create(
        document=doc_afib,
        chunk_index=1,
        page_number=2,
        section_title="DOAC Dosing & Pharmacotherapy",
        content=(
            "Direct Oral Anticoagulants (DOACs): For non-valvular atrial fibrillation, "
            "Rivaroxaban: Standard dose is 20 mg orally once daily taken with the evening meal "
            "(food is required to achieve consistent oral bioavailability). "
            "Dose reduction to 15 mg orally once daily is indicated for patients with moderate renal impairment "
            "(Creatinine Clearance CrCl 15 to 49 mL/min). "
            "Apixaban: Standard dose is 5 mg orally twice daily."
        ),
        token_count=80,
        bounding_box={"x0": 50, "y0": 100, "x1": 400, "y1": 250}
    )

    doc_copd = Document.objects.create(
        title="2026 GOLD Global Strategy for COPD",
        file="guidelines/copd.pdf",
        uploaded_by=clinician_user
    )
    c2 = Chunk.objects.create(
        document=doc_copd,
        chunk_index=1,
        page_number=1,
        section_title="Diagnosis & Spirometry Criteria",
        content=(
            "2026 GOLD Global Strategy for COPD: Spirometric Confirmation. "
            "A post-bronchodilator FEV1/FVC ratio < 0.70 is mandatory to confirm persistent airflow limitation. "
            "First-line maintenance dual bronchodilation with LAMA plus LABA is recommended."
        ),
        token_count=60,
        bounding_box={"x0": 60, "y0": 80, "x1": 420, "y1": 200}
    )
    return doc_afib, doc_copd


@pytest.mark.django_db
class TestIntentRoutingAndGroundedQA:
    def test_hello_returns_no_citations(self, clinician_user):
        """'hello' must return a natural greeting with no citations, confidence, or verification table."""
        res = QAService.ask_sync(query="hello", user=clinician_user)

        assert res["intent"] == IntentRouter.GREETING
        assert res["is_not_found"] is False
        assert len(res["citations"]) == 0
        assert len(res["verifications"]) == 0
        assert res["confidence_score"] is None
        assert "clinsaarthi" in res["answer"].lower() or "assist" in res["answer"].lower()

    def test_whats_up_returns_greeting_no_citations(self, clinician_user):
        """'whats up' must be routed to greeting, returning zero citations or hardcoded DOAC text."""
        res = QAService.ask_sync(query="whats up", user=clinician_user)

        assert res["intent"] == IntentRouter.GREETING
        assert len(res["citations"]) == 0
        assert len(res["verifications"]) == 0
        assert res["confidence_score"] is None
        assert "rivaroxaban" not in res["answer"].lower()
        assert "apixaban" not in res["answer"].lower()

    def test_who_won_world_cup_returns_off_topic_reply(self, clinician_user):
        """'who won the world cup' must return an off-topic explanation with no citations."""
        res = QAService.ask_sync(query="who won the world cup", user=clinician_user)

        assert res["intent"] == IntentRouter.OFF_TOPIC
        assert res["is_not_found"] is False
        assert len(res["citations"]) == 0
        assert len(res["verifications"]) == 0
        assert res["confidence_score"] is None
        # Must clearly explain clinical scope and inability to answer general trivia
        ans_lower = res["answer"].lower()
        assert "guideline" in ans_lower or "clinical" in ans_lower or "medical" in ans_lower
        assert "unable" in ans_lower or "cannot" in ans_lower or "trivia" in ans_lower

    def test_rivaroxaban_question_returns_only_rivaroxaban_rows(self, clinician_user, afib_and_copd_guidelines):
        """
        The Rivaroxaban question must return an answer addressing only the asked question,
        and verification rows must contain ONLY Rivaroxaban.
        """
        doc_afib, _ = afib_and_copd_guidelines
        query = "What is the recommended dose of Rivaroxaban for Atrial Fibrillation with normal renal function?"
        res = QAService.ask_sync(query=query, user=clinician_user, document_ids=[str(doc_afib.id)])
        assert res["intent"] == IntentRouter.MEDICAL
        assert res["is_not_found"] is False
        assert "rivaroxaban" in res["answer"].lower()
        assert "20 mg" in res["answer"].lower() or "20" in res["answer"]
        assert len(res["citations"]) > 0

        # Verification rows must contain ONLY Rivaroxaban (no Apixaban or Dabigatran rows!)
        assert len(res["verifications"]) > 0
        verified_drugs = [v["drug_name"].lower() for v in res["verifications"]]
        assert all(drug == "rivaroxaban" for drug in verified_drugs)
        assert "apixaban" not in verified_drugs
        assert "dabigatran" not in verified_drugs

    def test_two_different_medical_questions_return_different_answers(self, clinician_user, afib_and_copd_guidelines):
        """Two different medical questions must return distinctly different answers."""
        doc_afib, doc_copd = afib_and_copd_guidelines

        q1 = "What is the recommended dose of Rivaroxaban for Atrial Fibrillation with normal renal function?"
        res1 = QAService.ask_sync(query=q1, user=clinician_user, document_ids=[str(doc_afib.id)])

        q2 = "What is the post-bronchodilator spirometry criterion for COPD?"
        res2 = QAService.ask_sync(query=q2, user=clinician_user, document_ids=[str(doc_copd.id)])

        assert res1["is_not_found"] is False
        assert res2["is_not_found"] is False
        assert res1["answer"] != res2["answer"]

        assert "rivaroxaban" in res1["answer"].lower()
        assert "fev1" in res2["answer"].lower() or "copd" in res2["answer"].lower()

    def test_confidence_gate_rejection_suggests_rephrasing(self, clinician_user, afib_and_copd_guidelines):
        """Unsupported clinical query must fail confidence gate with real rerank score and rephrase advice."""
        doc_afib, _ = afib_and_copd_guidelines
        unsupported = "What is the adjuvant chemotherapy regimen and radiation fractionation for glioblastoma multiforme?"
        res = QAService.ask_sync(query=unsupported, user=clinician_user, document_ids=[str(doc_afib.id)])

        assert res["is_not_found"] is True
        assert "not found in the provided documents" in res["answer"]
        assert "rephras" in res["answer"].lower()
        assert res["confidence_score"] is not None
        assert res["confidence_score"] < 0.50
        assert len(res["citations"]) == 0
        assert len(res["verifications"]) == 0

    def test_ask_endpoint_accepts_event_stream_header(self, clinician_user, afib_and_copd_guidelines):
        """Endpoint /api/v1/qa/ask/ must accept 'Accept: text/event-stream' without returning 406 Not Acceptable."""
        api_client = APIClient()
        api_client.force_authenticate(user=clinician_user)

        url = reverse("qa:ask_question")
        payload = {
            "question": "hello",
            "stream": True
        }
        response = api_client.post(url, payload, format="json", HTTP_ACCEPT="text/event-stream")

        assert response.status_code == status.HTTP_200_OK
        assert response.get("Content-Type") == "text/event-stream"
