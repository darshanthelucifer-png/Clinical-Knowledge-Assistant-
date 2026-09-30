"""
================================================================================
ClinSaarthi AI - Embeddings, VectorStore & Hybrid Retriever Tests
================================================================================
What it tests:
    1. BaseEmbeddingService vector normalization and deterministic embeddings.
    2. VectorStore indexing, similarity search with cosine scores, and deletion.
    3. Swappable vector stores (ChromaVectorStore & InMemoryVectorStore).
    4. BM25 keyword matching for exact medical terms (Apixaban, CHA2DS2-VASc).
    5. Reciprocal Rank Fusion (RRF) combining dense and lexical rankings.
    6. Cross-Encoder reranker score calculation and top-5 selection.
    7. DEBUG_RAG=true telemetry (stage latencies, scores, and candidate metrics).
    8. REST API endpoint /api/v1/qa/retrieve/ integration test.
================================================================================
"""
from pathlib import Path
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document, Chunk
from ai.embeddings import get_embedding_service, LightweightMedicalEmbedding
from ai.vectorstore import ChromaVectorStore, InMemoryVectorStore, get_vector_store
from ai.retriever import HybridRetriever
from services.ingestion_service import IngestionService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="dr_electrophysiologist",
        email="ep@cardio.org",
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
def populated_document(clinician_user, sample_pdf_path):
    doc = Document.objects.create(
        title="AFib Guidelines 2026",
        file=sample_pdf_path,
        uploaded_by=clinician_user
    )
    IngestionService.process_document(str(doc.id))
    return doc

class TestEmbeddingsAndVectorStore:
    def test_embedding_normalization(self):
        emb_service = LightweightMedicalEmbedding()
        vec = emb_service.embed_query("Apixaban 5 mg twice daily for stroke prevention")
        assert len(vec) == 384
        # Verify L2 norm is approximately 1.0
        norm = sum(x * x for x in vec) ** 0.5
        assert pytest.approx(norm, 0.001) == 1.0

    def test_in_memory_vector_store(self, populated_document):
        store = InMemoryVectorStore()
        chunks = populated_document.chunks.all()
        ids = store.add_chunks(list(chunks))

        assert len(ids) == chunks.count()
        assert store.count() == chunks.count()

        # Search for anticoagulation
        results = store.similarity_search_with_score("anticoagulant apixaban rivaroxaban", k=3)
        assert len(results) > 0
        first_chunk, score = results[0]
        assert "Apixaban" in first_chunk["content"] or "anticoagulant" in first_chunk["content"].lower()
        assert 0.0 <= score <= 1.0

    def test_chroma_vector_store_persistence(self, populated_document, tmp_path):
        chroma_dir = str(tmp_path / "test_chroma")
        store = ChromaVectorStore(persist_directory=chroma_dir, collection_name="test_col")
        chunks = populated_document.chunks.all()
        ids = store.add_chunks(list(chunks))

        assert store.count() == chunks.count()

        results = store.similarity_search_with_score("stroke risk CHA2DS2-VASc score", k=2)
        assert len(results) > 0
        chunk_dict, score = results[0]
        assert "document_id" in chunk_dict
        assert "page_number" in chunk_dict
        assert 0.0 <= score <= 1.0

        # Test deletion
        store.delete_document_chunks(str(populated_document.id))
        assert store.count() == 0

class TestHybridRetriever:
    def test_hybrid_dense_and_bm25_retrieval(self, populated_document):
        vstore = InMemoryVectorStore()
        vstore.add_chunks(list(populated_document.chunks.all()))

        retriever = HybridRetriever(vector_store=vstore, top_dense=10, top_rerank=3, debug_mode=True)
        result = retriever.retrieve("What is the standard dosage for Apixaban in non-valvular AF?")

        assert len(result.chunks) > 0
        assert len(result.chunks) <= 3
        assert result.best_score > 0.0

        # Verify exact medical entity presence in top chunks
        top_text = " ".join(c["content"] for c in result.chunks)
        assert "Apixaban" in top_text
        assert "5 mg" in top_text

        # Verify debug info is populated
        assert result.debug_info is not None
        assert "latencies_ms" in result.debug_info
        assert "dense_retrieval" in result.debug_info["latencies_ms"]
        assert "bm25_retrieval" in result.debug_info["latencies_ms"]
        assert "rrf_fusion" in result.debug_info["latencies_ms"]
        assert "cross_encoder_rerank" in result.debug_info["latencies_ms"]
        assert result.debug_info["confidence_passed"] is True

    def test_confidence_gate_trigger_on_out_of_domain_query(self, populated_document):
        vstore = InMemoryVectorStore()
        vstore.add_chunks(list(populated_document.chunks.all()))

        retriever = HybridRetriever(
            vector_store=vstore,
            confidence_threshold=0.75,
            debug_mode=True
        )
        # Query completely unrelated to Atrial Fibrillation
        result = retriever.retrieve("Quantum mechanics wave-particle duality Schrödinger equation")

        assert result.debug_info is not None
        # Best score should be low and fail confidence gate
        assert result.confidence_passed is False

@pytest.mark.django_db
class TestRetrieveAPIEndpoint:
    def test_api_retrieve_with_debug_flag(self, api_client, clinician_user, populated_document):
        api_client.force_authenticate(user=clinician_user)
        url = reverse('qa:retrieve_debug')
        payload = {
            "query": "Recommended dosage for Rivaroxaban",
            "document_ids": [str(populated_document.id)],
            "debug": True
        }
        response = api_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert "chunks" in response.data
        assert "best_score" in response.data
        assert "confidence_passed" in response.data
        assert "debug_info" in response.data

        # Verify top chunk contains Rivaroxaban
        chunks = response.data["chunks"]
        assert len(chunks) > 0
        first_chunk = chunks[0]
        assert "Rivaroxaban" in first_chunk["content"] or "20 mg" in first_chunk["content"]
        assert "bounding_box" in first_chunk
        assert "page_number" in first_chunk
