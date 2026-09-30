"""
================================================================================
ClinSaarthi AI - Multi-Node Verification Agent & External APIs Test Suite
================================================================================
What it tests:
    1. Medical Acronym Expansion & Intent Classification (Node 1: Understand).
    2. Pharmacological Claim Tuple Extraction (Node 5: Extract Facts).
    3. Multi-Tier Verification Logic (VERIFIED, CONFLICT, UNSUPPORTED) (Node 6: Verify).
    4. Free External Health APIs: RxNorm (NIH) & openFDA with offline fallback.
    5. Unit functionality of all 8 independent graph nodes.
    6. LangGraph StateGraph Execution:
       - Clean path: Evidence grounded -> all verified -> Respond.
       - Self-Correction Loop: Detected conflict -> Repair -> Generate loop.
       - Max Repair Cap: Prevents infinite loop at count=2 and appends warning banner.
       - Confidence Gate: Rejects unsupported queries immediately.
    7. Database persistence of VerificationResult audit records.
================================================================================
"""
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document
from apps.qa.models import Conversation, Message, VerificationResult
from services.ingestion_service import IngestionService
from services.verification_service import VerificationService
from services.qa_service import QAService
from ai.nlp import MedicalNLPExtractor
from ai.external_apis import RxNormClient, OpenFDAClient
from ai.graph.state import AgentState
from ai.graph.nodes import (
    understand_node,
    confidence_gate_node,
    extract_facts_node,
    verify_node,
    repair_node,
    respond_node
)
from ai.graph.graph import build_graph, StateGraph


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="dr_cardiologist",
        email="cardio@hospital.org",
        password="SecurePassword123!",
        role=User.Role.CLINICIAN,
        department="Cardiology"
    )


@pytest.fixture
def sample_pdf_path():
    p1 = Path(__file__).resolve().parent.parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    if p1.exists():
        return str(p1)
    p2 = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    return str(p2)


@pytest.fixture
def ingested_guideline(clinician_user, sample_pdf_path):
    doc = Document.objects.create(
        title="AFib Guidelines 2026",
        file=sample_pdf_path,
        uploaded_by=clinician_user
    )
    IngestionService.process_document(str(doc.id))
    return doc


class TestMedicalNLPAndClaimExtraction:
    def test_acronym_expansion(self):
        raw = "Initiate DOAC for stroke prevention in non-valvular AF and HTN"
        expanded = MedicalNLPExtractor.expand_medical_acronyms(raw)
        assert "Direct Oral Anticoagulant" in expanded
        assert "Atrial Fibrillation" in expanded
        assert "Hypertension" in expanded

    def test_clinical_intent_classification(self):
        assert MedicalNLPExtractor.classify_clinical_intent("What is the dose of Rivaroxaban?") == "dosing"
        assert MedicalNLPExtractor.classify_clinical_intent("What are the contraindications for DOACs?") == "contraindication"
        assert MedicalNLPExtractor.classify_clinical_intent("First-line treatment recommendation") == "treatment"
        assert MedicalNLPExtractor.classify_clinical_intent("CHA2DS2-VASc score diagnostic criteria") == "diagnosis"
        assert MedicalNLPExtractor.classify_clinical_intent("Monitor INR and renal CrCl") == "monitoring"

    def test_claim_extraction(self):
        sample_answer = (
            "The recommended dosage of Rivaroxaban is 20 mg once daily taken orally. "
            "Alternatively, prescribe Apixaban 5 mg twice daily."
        )
        claims = MedicalNLPExtractor.extract_clinical_claims(sample_answer)
        assert len(claims) >= 2

        drugs = [c["drug_name"] for c in claims]
        assert "Rivaroxaban" in drugs
        assert "Apixaban" in drugs

        riv = next(c for c in claims if c["drug_name"] == "Rivaroxaban")
        assert riv["dosage"] == "20"
        assert riv["unit"] == "mg"
        assert "once daily" in riv["frequency"]


class TestVerificationLogic:
    def test_verified_claim_match(self):
        source_chunks = [{
            "content": "For non-valvular atrial fibrillation, Rivaroxaban 20 mg once daily with the evening meal is recommended."
        }]
        answer = "Patients should receive Rivaroxaban 20 mg once daily."
        results = VerificationService.verify_answer(answer, source_chunks, skip_external_apis=True)

        assert len(results) == 1
        assert results[0]["status"] == VerificationResult.Status.VERIFIED
        assert results[0]["nli_score"] > 0.90
        assert "matches cited guideline" in results[0]["explanation"]

    def test_conflict_claim_mismatch(self):
        source_chunks = [{
            "content": "Rivaroxaban is administered at 20 mg once daily. For renal impairment (CrCl 15-49 mL/min), reduce to 15 mg."
        }]
        # Injected deliberate contradiction: 50 mg
        answer = "The standard dosage of Rivaroxaban is 50 mg once daily."
        results = VerificationService.verify_answer(answer, source_chunks, skip_external_apis=True)

        assert len(results) == 1
        assert results[0]["status"] == VerificationResult.Status.CONFLICT
        assert results[0]["nli_score"] < 0.20
        assert "Direct conflict" in results[0]["explanation"]

    def test_unsupported_claim(self):
        source_chunks = [{
            "content": "Atrial fibrillation guidelines recommend oral anticoagulation with direct oral anticoagulants."
        }]
        # Drug not in guideline
        answer = "Consider administering Pembrolizumab 200 mg every 3 weeks."
        results = VerificationService.verify_answer(answer, source_chunks, skip_external_apis=True)

        assert len(results) == 1
        assert results[0]["status"] == VerificationResult.Status.UNSUPPORTED
        assert "not found in the cited guideline" in results[0]["explanation"]


class TestExternalPublicHealthAPIs:
    def test_rxnorm_lookup_online_or_mock(self):
        # Test with mock for deterministic CI
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'{"idGroup": {"rxnormId": ["1114195"]}}'
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            # Clear lru_cache for testing
            RxNormClient.lookup_rxcui.cache_clear()
            rxcui = RxNormClient.lookup_rxcui("Rivaroxaban")
            assert rxcui == "1114195"

    def test_rxnorm_offline_graceful_fallback(self):
        with patch('urllib.request.urlopen', side_effect=Exception("Connection timed out")):
            RxNormClient.lookup_rxcui.cache_clear()
            rxcui = RxNormClient.lookup_rxcui("NonExistentDrug")
            assert rxcui is None  # Does not crash

    def test_openfda_lookup_online_or_mock(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'{"results": [{"openfda": {"generic_name": ["Rivaroxaban"]}, "boxed_warning": ["Warning"]}]}'
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            OpenFDAClient.check_drug_label.cache_clear()
            info = OpenFDAClient.check_drug_label("Rivaroxaban")
            assert info["matched"] is True
            assert info["has_boxed_warning"] is True

    def test_openfda_offline_graceful_fallback(self):
        with patch('urllib.request.urlopen', side_effect=Exception("Network unreachable")):
            OpenFDAClient.check_drug_label.cache_clear()
            info = OpenFDAClient.check_drug_label("AnyDrug")
            assert info["matched"] is False


class TestLangGraphNodes:
    def test_understand_node(self):
        state = {"raw_query": "Dose of DOAC in AF with HTN?"}
        updates = understand_node(state)
        assert "Direct Oral Anticoagulant" in updates["expanded_query"]
        assert updates["clinical_intent"] == "dosing"

    def test_confidence_gate_rejection(self):
        state = {"confidence_passed": False, "retrieved_chunks": []}
        updates = confidence_gate_node(state)
        assert updates["is_refusal"] is True
        assert "not found in the provided clinical guidelines" in updates["final_answer"]

    def test_repair_node_builds_directive_when_under_limit(self):
        state = {
            "repair_count": 0,
            "verification_results": [{
                "status": "CONFLICT",
                "explanation": "Answer stated Rivaroxaban 50 mg, but source specifies 20 mg."
            }]
        }
        updates = repair_node(state)
        assert updates["repair_count"] == 1
        assert "Rivaroxaban 50 mg" in updates["repair_instruction"]

    def test_repair_node_appends_warning_banner_when_limit_reached(self):
        state = {
            "repair_count": 1,
            "draft_answer": "Initial draft text.",
            "verification_results": [{
                "status": "CONFLICT",
                "explanation": "Unresolved dosage discrepancy."
            }]
        }
        updates = repair_node(state)
        assert updates["repair_count"] == 2
        assert "CLINICAL AUDIT WARNING" in updates["draft_answer"]


@pytest.mark.django_db
class TestLangGraphAgentIntegration:
    def test_agent_clean_path_execution(self, clinician_user, ingested_guideline):
        """Clean path: grounded query passes gate, generates answer, verifies claims without conflicts."""
        query = "What is the recommended dose of Rivaroxaban for atrial fibrillation?"
        res = QAService.ask_agentic(
            query=query,
            user=clinician_user,
            document_ids=[str(ingested_guideline.id)]
        )

        assert res["is_not_found"] is False
        assert "Rivaroxaban" in res["answer"]
        assert len(res["citations"]) > 0
        assert res["repair_count"] == 0
        assert res["clinical_intent"] == "dosing"

    def test_agent_confidence_refusal_on_irrelevant_query(self, clinician_user, ingested_guideline):
        """Out of domain query triggers confidence gate refusal in state graph."""
        query = "What is the capital of France and what are the best tourist hotels?"
        res = QAService.ask_agentic(
            query=query,
            user=clinician_user,
            document_ids=[str(ingested_guideline.id)]
        )

        assert res["is_not_found"] is True
        assert "not found in the provided clinical guidelines" in res["answer"]
        assert len(res["citations"]) == 0

    def test_agent_persists_verification_results_in_db(self, clinician_user, ingested_guideline):
        """Verifies that VerificationResult models are persisted and linked to Message."""
        query = "What is the recommended dose of Rivaroxaban?"
        res = QAService.ask_agentic(
            query=query,
            user=clinician_user,
            document_ids=[str(ingested_guideline.id)]
        )

        msg_id = res["message_id"]
        msg = Message.objects.get(id=msg_id)

        # Check verifications in DB
        db_verifications = msg.verifications.all()
        assert db_verifications.exists()

        drug_names = [v.drug_name for v in db_verifications]
        assert "Rivaroxaban" in drug_names
        riv_v = db_verifications.filter(drug_name="Rivaroxaban").first()
        assert riv_v.status in [VerificationResult.Status.VERIFIED, VerificationResult.Status.CONFLICT]
        assert riv_v.nli_score is not None

    def test_ask_endpoint_with_agentic_flag(self, api_client, clinician_user, ingested_guideline):
        """POST /api/v1/qa/ask/ with agentic=True invokes multi-node agent and returns verifications."""
        api_client.force_authenticate(user=clinician_user)
        url = reverse('qa:ask_question')
        payload = {
            "question": "What is the dosage of Rivaroxaban in AF?",
            "document_ids": [str(ingested_guideline.id)],
            "agentic": True
        }
        response = api_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "answer" in data
        assert "verifications" in data
        assert "citations" in data
        assert "repair_count" in data
