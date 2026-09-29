"""RAG Service - Knowledge retrieval using vector similarity search."""

import numpy as np
from typing import Optional
from sqlalchemy.orm import Session
from packages.database.models import KnowledgeDocument, KnowledgeChunk
from packages.observability.logging import get_logger, track_latency

logger = get_logger("rag")


class VectorStore:
    """Abstract vector store interface."""

    def __init__(self):
        self._embeddings: list[np.ndarray] = []
        self._metadata: list[dict] = []
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                logger.warning("sentence-transformers not installed, using random embeddings")
                self._model = "mock"
        return self._model

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        model = self._get_model()
        if model == "mock":
            # Deterministic mock embedding based on text hash
            np.random.seed(hash(text) % 2**31)
            return np.random.randn(384).astype(np.float32)
        return model.encode(text, normalize_embeddings=True)

    def add(self, text: str, metadata: dict):
        """Add a document to the vector store."""
        embedding = self.embed(text)
        self._embeddings.append(embedding)
        self._metadata.append({**metadata, "text": text})

    def search(self, query: str, top_k: int = 5, filter_fn=None) -> list[dict]:
        """Search for similar documents."""
        if not self._embeddings:
            return []

        query_embedding = self.embed(query)
        similarities = []

        for i, emb in enumerate(self._embeddings):
            if filter_fn and not filter_fn(self._metadata[i]):
                continue
            sim = float(np.dot(query_embedding, emb))
            similarities.append((sim, i))

        similarities.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, idx in similarities[:top_k]:
            result = {**self._metadata[idx], "similarity": round(sim, 4)}
            results.append(result)

        return results

    def clear(self):
        """Clear all stored embeddings."""
        self._embeddings.clear()
        self._metadata.clear()

    @property
    def size(self) -> int:
        return len(self._embeddings)


# Singleton vector store
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


class RAGService:
    """Retrieval-Augmented Generation service for business knowledge."""

    def __init__(self, db: Session, vector_store: Optional[VectorStore] = None):
        self.db = db
        self.vector_store = vector_store or get_vector_store()

    def index_knowledge(self):
        """Index all knowledge documents into the vector store."""
        docs = self.db.query(KnowledgeDocument).all()
        self.vector_store.clear()

        for doc in docs:
            self.vector_store.add(
                text=doc.content,
                metadata={
                    "document_id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "business_domain": doc.business_domain,
                    "table_name": doc.table_name,
                    "column_name": doc.column_name,
                },
            )

        logger.info("knowledge_indexed", count=len(docs))
        return len(docs)

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> list[dict]:
        """Search for relevant business knowledge."""
        if self.vector_store.size == 0:
            self.index_knowledge()

        filter_fn = None
        if category or table_name:
            def filter_fn(meta):
                if category and meta.get("category") != category:
                    return False
                if table_name and meta.get("table_name") != table_name:
                    return False
                return True

        results = self.vector_store.search(query, top_k=top_k, filter_fn=filter_fn)
        logger.info("knowledge_searched", query=query[:100], results=len(results))
        return results

    def get_all_documents(
        self,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        search_text: Optional[str] = None,
    ) -> list[KnowledgeDocument]:
        """Get knowledge documents with optional filtering."""
        query = self.db.query(KnowledgeDocument)
        if category:
            query = query.filter(KnowledgeDocument.category == category)
        if domain:
            query = query.filter(KnowledgeDocument.business_domain == domain)
        if search_text:
            query = query.filter(
                KnowledgeDocument.content.ilike(f"%{search_text}%")
                | KnowledgeDocument.title.ilike(f"%{search_text}%")
            )
        return query.order_by(KnowledgeDocument.created_at.desc()).all()

    def add_document(
        self,
        title: str,
        content: str,
        category: str,
        business_domain: Optional[str] = None,
        table_name: Optional[str] = None,
        column_name: Optional[str] = None,
    ) -> KnowledgeDocument:
        """Add a new knowledge document."""
        doc = KnowledgeDocument(
            title=title,
            content=content,
            category=category,
            business_domain=business_domain,
            table_name=table_name,
            column_name=column_name,
        )
        self.db.add(doc)
        self.db.flush()

        # Add to vector store
        self.vector_store.add(
            text=content,
            metadata={
                "document_id": doc.id,
                "title": title,
                "category": category,
                "business_domain": business_domain,
                "table_name": table_name,
                "column_name": column_name,
            },
        )

        logger.info("knowledge_document_added", title=title, category=category)
        return doc
