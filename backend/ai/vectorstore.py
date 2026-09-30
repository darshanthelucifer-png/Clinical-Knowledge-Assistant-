"""
================================================================================
ClinSaarthi AI - Swappable Vector Store Engine
================================================================================
What it does:
    Provides an enterprise vector database abstraction. Connects to ChromaDB
    (persisted in `data/chroma_db/`) as primary vector database, with an in-memory
    vector store as a swappable fallback. Stores chunk embeddings, spatial bounding
    boxes, section titles, and page numbers for visual citation retrieval.

Python Concepts Demonstrated:
    1. Abstract Base Classes (abc.ABC, @abstractmethod): Contract enforcement.
    2. Factory Pattern: Instantiating vector store implementations dynamically.
    3. Mathematical Cosine Distance to Cosine Similarity Conversion:
       score = 1.0 - distance (or normalized range 0.0 to 1.0).
================================================================================
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import json
import os
from pathlib import Path
from django.conf import settings
from .embeddings import get_embedding_service, BaseEmbeddingService

class BaseVectorStore(ABC):
    """Abstract interface defining vector store capabilities."""

    @abstractmethod
    def add_chunks(self, chunks: List[Any]) -> List[str]:
        """Indexes a collection of Chunk instances or ChunkPayloads."""
        pass

    @abstractmethod
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 20,
        document_filter: Optional[List[str]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Returns top k chunks matching query.
        Returns tuples of: (chunk_metadata_and_content_dict, similarity_score_between_0_and_1)
        """
        pass

    @abstractmethod
    def delete_document_chunks(self, document_id: str) -> None:
        """Deletes all indexed vectors associated with a specific document ID."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns the total number of indexed vectors."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB implementation persisting vectors locally in data/chroma_db.
    """
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "clinical_guidelines",
        embedding_service: Optional[BaseEmbeddingService] = None
    ):
        self.persist_directory = persist_directory or getattr(
            settings, 'CHROMA_PERSIST_DIRECTORY', str(settings.BASE_DIR.parent / 'data' / 'chroma_db')
        )
        self.collection_name = collection_name
        self.embedding_service = embedding_service or get_embedding_service()

        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        import chromadb
        from chromadb.config import Settings
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Any]) -> List[str]:
        if not chunks:
            return []

        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            c_id = str(chunk.id) if hasattr(chunk, 'id') else f"chk_{chunk.page_number}_{chunk.chunk_index}"
            content = chunk.content
            doc_id = str(chunk.document_id) if hasattr(chunk, 'document_id') else str(getattr(chunk, 'document', ''))
            page = chunk.page_number
            section = chunk.section_title or "General"
            token_count = chunk.token_count
            bbox = chunk.bounding_box if hasattr(chunk, 'bounding_box') else {}

            ids.append(c_id)
            texts.append(content)
            metadatas.append({
                "document_id": doc_id,
                "page_number": int(page),
                "section_title": str(section),
                "token_count": int(token_count),
                "bounding_box": json.dumps(bbox),
            })

        # Generate dense embeddings
        embeddings = self.embedding_service.embed_documents(texts)

        # Upsert in ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return ids

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 20,
        document_filter: Optional[List[str]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        if self.count() == 0:
            return []

        query_emb = self.embedding_service.embed_query(query)
        where_clause = None
        if document_filter:
            doc_filter_strs = [str(d) for d in document_filter]
            if len(doc_filter_strs) == 1:
                where_clause = {"document_id": doc_filter_strs[0]}
            else:
                where_clause = {"document_id": {"$in": doc_filter_strs}}

        actual_k = min(k, self.count())
        if actual_k <= 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=actual_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        output: List[Tuple[Dict[str, Any], float]] = []
        if not results or not results["documents"] or not results["documents"][0]:
            return output

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
        ids = results["ids"][0]

        for doc_text, meta, dist, chunk_id in zip(docs, metas, distances, ids):
            # Chroma with cosine distance: distance in [0, 2].
            # Convert to similarity in [0, 1]: sim = 1.0 - (dist / 2.0)
            similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
            bbox = {}
            if "bounding_box" in meta and meta["bounding_box"]:
                try:
                    bbox = json.loads(meta["bounding_box"])
                except Exception:
                    pass

            chunk_dict = {
                "chunk_id": chunk_id,
                "content": doc_text,
                "document_id": meta.get("document_id", ""),
                "page_number": meta.get("page_number", 1),
                "section_title": meta.get("section_title", ""),
                "token_count": meta.get("token_count", 0),
                "bounding_box": bbox,
            }
            output.append((chunk_dict, round(similarity, 4)))

        # Sort descending by similarity score
        output.sort(key=lambda x: x[1], reverse=True)
        return output

    def delete_document_chunks(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception:
            pass

    def count(self) -> int:
        return self.collection.count()


class InMemoryVectorStore(BaseVectorStore):
    """
    Swappable in-memory vector store alternative.
    Useful for isolated testing, FAISS-like operations, or environments where
    disk persistence is disabled.
    """
    def __init__(self, embedding_service: Optional[BaseEmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()
        self.store: Dict[str, Dict[str, Any]] = {}

    def add_chunks(self, chunks: List[Any]) -> List[str]:
        if not chunks:
            return []

        ids: List[str] = []
        texts: List[str] = []
        for c in chunks:
            c_id = str(c.id) if hasattr(c, 'id') else f"mem_{c.page_number}_{c.chunk_index}"
            ids.append(c_id)
            texts.append(c.content)

        embeddings = self.embedding_service.embed_documents(texts)

        for chunk, c_id, emb in zip(chunks, ids, embeddings):
            doc_id = str(chunk.document_id) if hasattr(chunk, 'document_id') else str(getattr(chunk, 'document', ''))
            bbox = chunk.bounding_box if hasattr(chunk, 'bounding_box') else {}

            self.store[c_id] = {
                "chunk_id": c_id,
                "content": chunk.content,
                "document_id": doc_id,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title or "General",
                "token_count": chunk.token_count,
                "bounding_box": bbox,
                "embedding": emb
            }

        return ids

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        return max(0.0, min(1.0, (dot + 1.0) / 2.0))

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 20,
        document_filter: Optional[List[str]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not self.store:
            return []

        q_emb = self.embedding_service.embed_query(query)
        scored: List[Tuple[Dict[str, Any], float]] = []
        filter_set = {str(d) for d in document_filter} if document_filter else None

        for item in self.store.values():
            if filter_set and str(item["document_id"]) not in filter_set:
                continue

            sim = self._cosine_similarity(q_emb, item["embedding"])
            # Return item copy without embedding
            item_copy = {k: v for k, v in item.items() if k != "embedding"}
            scored.append((item_copy, round(sim, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def delete_document_chunks(self, document_id: str) -> None:
        self.store = {k: v for k, v in self.store.items() if v["document_id"] != document_id}

    def count(self) -> int:
        return len(self.store)


def get_vector_store() -> BaseVectorStore:
    """
    Factory function returning the active vector store based on VECTOR_STORE_PROVIDER.
    Defaults to ChromaVectorStore.
    """
    provider = getattr(settings, 'VECTOR_STORE_PROVIDER', 'chroma').lower()
    if provider == 'chroma':
        try:
            return ChromaVectorStore()
        except Exception:
            # Fallback to in-memory if Chroma initialization fails in environment
            return InMemoryVectorStore()
    return InMemoryVectorStore()
