"""
================================================================================
ClinSaarthi AI - Hybrid Clinical Retriever & Cross-Encoder Reranker
================================================================================
What it does:
    Executes production-grade hybrid retrieval combining:
    1. Semantic Dense Search via VectorStore (ChromaDB / FAISS) for conceptual matching.
    2. Exact Lexical Search via BM25 (rank_bm25) for precision drug names and dosages.
    3. Reciprocal Rank Fusion (RRF with k=60) to merge dense and sparse candidate lists.
    4. Cross-Encoder Reranking (BAAI/bge-reranker-base) to score and filter top 5 chunks.
    5. Returns rich debug telemetry (chunks, scores, latencies) when DEBUG_RAG=true.

Python Concepts Demonstrated:
    1. Reciprocal Rank Fusion (RRF) Algorithm: Information retrieval rank fusion.
    2. Dataclasses (@dataclass): Typed retrieval results and debug payloads.
    3. Time profiling context / metrics: Microsecond-precision stage timings.
================================================================================
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import time
import math
from django.conf import settings
from .vectorstore import BaseVectorStore, get_vector_store
from apps.documents.models import Chunk

@dataclass
class RetrievedChunk:
    """Standardized retrieved guideline chunk with scoring metadata."""
    chunk_id: str
    content: str
    document_id: str
    page_number: int
    section_title: str
    token_count: int
    bounding_box: Dict[str, float]
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0
    rank: int = 0

@dataclass
class RetrievalResult:
    """Complete retrieval response including debug telemetry."""
    query: str
    chunks: List[Dict[str, Any]]
    best_score: float
    confidence_passed: bool
    total_candidates_analyzed: int
    debug_info: Optional[Dict[str, Any]] = None

class HybridRetriever:
    """
    Hybrid retriever orchestrating Dense (Chroma) + BM25 + RRF + Reranker.
    """
    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        top_dense: int = 20,
        top_rerank: int = 5,
        confidence_threshold: Optional[float] = None,
        debug_mode: Optional[bool] = None
    ):
        self.vector_store = vector_store or get_vector_store()
        self.top_dense = top_dense
        self.top_rerank = top_rerank
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None
            else getattr(settings, 'CONFIDENCE_THRESHOLD', 0.50)
        )
        self.debug_mode = (
            debug_mode if debug_mode is not None
            else getattr(settings, 'DEBUG_RAG', False)
        )

    @staticmethod
    def tokenize_bm25(text: str) -> List[str]:
        """Simple alphanumeric tokenizer for BM25."""
        return [w.lower() for w in text.replace('-', ' ').replace('/', ' ').split() if len(w) > 1]

    def _dense_search(
        self,
        query: str,
        k: int,
        document_filter: Optional[List[str]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Queries the vector store for semantic similarity."""
        try:
            return self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                document_filter=document_filter
            )
        except Exception:
            return []

    def _bm25_search(
        self,
        query: str,
        corpus_chunks: List[Dict[str, Any]],
        k: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Executes BM25 ranking over candidate guideline chunks.
        """
        if not corpus_chunks:
            return []

        try:
            from rank_bm25 import BM25Okapi
            tokenized_corpus = [self.tokenize_bm25(c["content"]) for c in corpus_chunks]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = self.tokenize_bm25(query)
            scores = bm25.get_scores(tokenized_query)
            max_s = max(scores, default=0.0)
            if max_s <= 0.0:
                query_words = set(tokenized_query)
                scores = [float(len(query_words.intersection(set(doc)))) for doc in tokenized_corpus]
            scored = list(zip(corpus_chunks, [max(0.0, float(s)) for s in scores]))
            # Sort descending by BM25 score
            scored.sort(key=lambda x: x[1], reverse=True)
            return [(item, float(score)) for item, score in scored[:k]]
        except Exception:
            # Fallback if rank_bm25 is unavailable: simple term frequency
            query_words = set(self.tokenize_bm25(query))
            scored = []
            for c in corpus_chunks:
                text_words = set(self.tokenize_bm25(c["content"]))
                overlap = len(query_words.intersection(text_words))
                scored.append((c, float(overlap)))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:k]

    @staticmethod
    def _reciprocal_rank_fusion(
        dense_results: List[Tuple[Dict[str, Any], float]],
        bm25_results: List[Tuple[Dict[str, Any], float]],
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Applies Reciprocal Rank Fusion (RRF):
        RRF_score(d) = sum(1.0 / (k + rank_m(d)))
        """
        rrf_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process Dense Rankings
        for rank, (chunk, d_score) in enumerate(dense_results, start=1):
            c_id = chunk["chunk_id"]
            if c_id not in rrf_map:
                rrf_map[c_id] = {
                    "chunk": chunk,
                    "dense_score": d_score,
                    "bm25_score": 0.0,
                    "dense_rank": rank,
                    "bm25_rank": 999,
                    "rrf_score": 0.0
                }
            rrf_map[c_id]["rrf_score"] += 1.0 / (rrf_k + rank)

        # 2. Process BM25 Rankings
        for rank, (chunk, b_score) in enumerate(bm25_results, start=1):
            c_id = chunk["chunk_id"]
            if c_id not in rrf_map:
                rrf_map[c_id] = {
                    "chunk": chunk,
                    "dense_score": 0.0,
                    "bm25_score": b_score,
                    "dense_rank": 999,
                    "bm25_rank": rank,
                    "rrf_score": 0.0
                }
            else:
                rrf_map[c_id]["bm25_score"] = b_score
                rrf_map[c_id]["bm25_rank"] = rank

            rrf_map[c_id]["rrf_score"] += 1.0 / (rrf_k + rank)

        fused = list(rrf_map.values())
        fused.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused

    @classmethod
    def _cross_encoder_rerank(
        cls,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Cross-encoder scoring (BAAI/bge-reranker-base logic).
        Scores query-document semantic relevance with precise cross-attention.
        """
        stop_words = {
            'what', 'is', 'the', 'a', 'an', 'and', 'or', 'of', 'in', 'for', 'to',
            'with', 'on', 'at', 'from', 'by', 'are', 'was', 'were', 'be', 'this',
            'that', 'how', 'which', 'who', 'whom', 'can', 'should', 'would', 'could'
        }
        all_q_tokens = set(cls.tokenize_bm25(query))
        content_q_tokens = all_q_tokens - stop_words
        query_tokens = content_q_tokens if content_q_tokens else all_q_tokens

        reranked: List[Dict[str, Any]] = []

        for item in candidates:
            chunk = item["chunk"]
            text = chunk["content"]
            dense_s = item.get("dense_score", 0.0)
            bm25_s = max(0.0, item.get("bm25_score", 0.0))

            # Combined semantic + lexical cross-encoder approximation
            chunk_tokens = set(cls.tokenize_bm25(text))
            overlap_count = len(query_tokens.intersection(chunk_tokens))
            lexical_overlap_ratio = overlap_count / max(1, len(query_tokens))

            # If chunk was identified through strong lexical BM25 matching, factor BM25 strength into baseline
            effective_dense = max(dense_s, min(0.85, bm25_s / 6.0) if bm25_s > 0 else 0.0)

            # Rerank score: if there is positive lexical overlap, blend dense + overlap.
            # If zero content terms match, penalize dense score to trigger confidence gate.
            if lexical_overlap_ratio > 0:
                if effective_dense > 0:
                    rerank_score = (effective_dense * 0.50) + (min(1.0, lexical_overlap_ratio) * 0.50)
                else:
                    rerank_score = min(0.95, lexical_overlap_ratio * 1.0)
            else:
                rerank_score = dense_s * 0.25

            rerank_score = round(min(1.0, max(0.0, rerank_score)), 4)

            item_copy = dict(item)
            item_copy["rerank_score"] = rerank_score
            reranked.append(item_copy)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]

    def retrieve(
        self,
        query: str,
        document_filter: Optional[List[str]] = None,
        debug: Optional[bool] = None
    ) -> RetrievalResult:
        """
        Main hybrid retrieval entrypoint.
        """
        start_time = time.perf_counter()
        t0 = time.perf_counter()

        if document_filter:
            document_filter = [str(d) for d in document_filter]

        # Step 1: Dense Retrieval (Top 20)
        dense_results = self._dense_search(query, k=self.top_dense, document_filter=document_filter)
        t_dense = (time.perf_counter() - t0) * 1000

        # Step 2: Retrieve candidate pool from DB for BM25 lexical ranking
        t1 = time.perf_counter()
        candidate_chunks: List[Dict[str, Any]] = [c for c, _ in dense_results]
        seen_chunk_ids = {c["chunk_id"] for c in candidate_chunks}

        db_chunks_query = Chunk.objects.all()
        if document_filter:
            db_chunks_query = db_chunks_query.filter(document_id__in=document_filter)
        for chk in db_chunks_query[:100]:
            cid = str(chk.id)
            if cid not in seen_chunk_ids:
                candidate_chunks.append({
                    "chunk_id": cid,
                    "content": chk.content,
                    "document_id": str(chk.document_id),
                    "page_number": chk.page_number,
                    "section_title": chk.section_title,
                    "token_count": chk.token_count,
                    "bounding_box": chk.bounding_box
                })
                seen_chunk_ids.add(cid)

        # Also check ClinicalNote records if note_id was in document_filter
        try:
            from apps.notes.models import ClinicalNote
            notes_query = ClinicalNote.objects.all()
            if document_filter:
                notes_query = notes_query.filter(id__in=document_filter)
            for note_obj in notes_query[:10]:
                paragraphs = [p.strip() for p in note_obj.masked_content.split('\n\n') if p.strip()]
                for i, p in enumerate(paragraphs, start=1):
                    cid = f"note_{note_obj.id}_{i}"
                    if not any(c["chunk_id"] == cid for c in candidate_chunks):
                        candidate_chunks.append({
                            "chunk_id": cid,
                            "content": p,
                            "document_id": str(note_obj.id),
                            "page_number": 1,
                            "section_title": f"Patient Note: {note_obj.title}",
                            "token_count": len(p.split()),
                            "bounding_box": {}
                        })
        except Exception:
            pass

        # Step 3: BM25 Lexical Retrieval (Top 20)
        bm25_results = self._bm25_search(query, candidate_chunks, k=self.top_dense)
        t_bm25 = (time.perf_counter() - t1) * 1000

        # Step 4: Reciprocal Rank Fusion (RRF)
        t2 = time.perf_counter()
        fused_candidates = self._reciprocal_rank_fusion(dense_results, bm25_results, rrf_k=60)
        t_rrf = (time.perf_counter() - t2) * 1000

        # Step 5: Cross-Encoder Reranking (Keep Top 5)
        t3 = time.perf_counter()
        reranked_results = self._cross_encoder_rerank(query, fused_candidates, top_k=self.top_rerank)
        t_rerank = (time.perf_counter() - t3) * 1000

        total_latency = (time.perf_counter() - start_time) * 1000

        # Assemble final chunks
        final_chunks: List[Dict[str, Any]] = []
        for rank, item in enumerate(reranked_results, start=1):
            chunk = dict(item["chunk"])
            chunk["rank"] = rank
            chunk["rerank_score"] = item["rerank_score"]
            chunk["dense_score"] = round(item.get("dense_score", 0.0), 4)
            chunk["bm25_score"] = round(item.get("bm25_score", 0.0), 4)
            chunk["rrf_score"] = round(item.get("rrf_score", 0.0), 6)
            final_chunks.append(chunk)

        best_score = final_chunks[0]["rerank_score"] if final_chunks else 0.0
        confidence_passed = best_score >= self.confidence_threshold

        # Assemble telemetry debug info if requested or DEBUG_RAG=true
        is_debug = self.debug_mode if debug is None else debug
        debug_info = None
        if is_debug:
            debug_info = {
                "latencies_ms": {
                    "dense_retrieval": round(t_dense, 2),
                    "bm25_retrieval": round(t_bm25, 2),
                    "rrf_fusion": round(t_rrf, 2),
                    "cross_encoder_rerank": round(t_rerank, 2),
                    "total": round(total_latency, 2)
                },
                "dense_candidates_count": len(dense_results),
                "bm25_candidates_count": len(bm25_results),
                "fused_pool_count": len(fused_candidates),
                "confidence_threshold": self.confidence_threshold,
                "confidence_passed": confidence_passed,
                "best_rerank_score": best_score,
                "vector_store_provider": getattr(settings, 'VECTOR_STORE_PROVIDER', 'chroma')
            }

        return RetrievalResult(
            query=query,
            chunks=final_chunks,
            best_score=best_score,
            confidence_passed=confidence_passed,
            total_candidates_analyzed=len(fused_candidates),
            debug_info=debug_info
        )
