"""Memory Service - persistent conversational and analytical memory."""

import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from packages.database.models import Memory, MemoryType
from packages.observability.logging import get_logger
from services.rag.service import get_vector_store, VectorStore

logger = get_logger("memory")


class MemoryService:
    """Persistent memory management for the business assistant."""

    def __init__(self, db: Session, vector_store: Optional[VectorStore] = None):
        self.db = db
        self.vector_store = vector_store or get_vector_store()

    def store_memory(
        self,
        user_id: int,
        content: str,
        memory_type: str = "insight",
        summary: Optional[str] = None,
        conversation_id: Optional[int] = None,
        entities: Optional[list[str]] = None,
        importance_score: float = 0.5,
        confidence: float = 0.8,
        metadata: Optional[dict] = None,
    ) -> Memory:
        """Store a new memory."""
        memory = Memory(
            user_id=user_id,
            conversation_id=conversation_id,
            memory_type=memory_type,
            content=content,
            summary=summary or content[:200],
            entities_json=entities or [],
            importance_score=importance_score,
            confidence=confidence,
            metadata_json=metadata or {},
        )
        self.db.add(memory)
        self.db.flush()

        logger.info(
            "memory_stored",
            memory_id=memory.id,
            memory_type=memory_type,
            importance=importance_score,
        )
        return memory

    def search_memories(
        self,
        query: str,
        user_id: int,
        top_k: int = 5,
        memory_type: Optional[str] = None,
    ) -> list[dict]:
        """Search memories using semantic similarity + ranking."""
        # Get user's memories
        q = self.db.query(Memory).filter(Memory.user_id == user_id)
        if memory_type:
            q = q.filter(Memory.memory_type == memory_type)
        q = q.filter(
            (Memory.expires_at.is_(None)) | (Memory.expires_at > datetime.utcnow())
        )

        memories = q.order_by(Memory.created_at.desc()).limit(100).all()

        if not memories:
            return []

        # Compute semantic similarity
        query_emb = self.vector_store.embed(query)
        scored = []

        for mem in memories:
            mem_emb = self.vector_store.embed(mem.content[:500])
            semantic_sim = float(np.dot(query_emb, mem_emb))

            # Recency score (decay over 30 days)
            age_days = (datetime.utcnow() - mem.created_at).days
            recency_score = max(0, 1.0 - (age_days / 30.0))

            # Combined score
            score = (
                semantic_sim * 0.6
                + recency_score * 0.2
                + mem.importance_score * 0.2
            )

            scored.append({
                "memory_id": mem.id,
                "content": mem.content,
                "summary": mem.summary,
                "memory_type": mem.memory_type,
                "importance_score": mem.importance_score,
                "created_at": mem.created_at.isoformat(),
                "entities": mem.entities_json,
                "score": round(score, 4),
            })

        # Sort by combined score
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Update last_accessed_at for top results
        top_ids = [m["memory_id"] for m in scored[:top_k]]
        if top_ids:
            self.db.query(Memory).filter(Memory.id.in_(top_ids)).update(
                {Memory.last_accessed_at: datetime.utcnow()},
                synchronize_session=False,
            )

        logger.info("memory_searched", query=query[:100], results=len(scored[:top_k]))
        return scored[:top_k]

    def get_user_memories(
        self,
        user_id: int,
        memory_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[Memory]:
        """Get all memories for a user."""
        q = self.db.query(Memory).filter(Memory.user_id == user_id)
        if memory_type:
            q = q.filter(Memory.memory_type == memory_type)
        return q.order_by(Memory.created_at.desc()).limit(limit).all()

    def delete_memory(self, memory_id: int, user_id: int) -> bool:
        """Delete a memory (users can only delete their own)."""
        mem = self.db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id,
        ).first()
        if mem:
            self.db.delete(mem)
            logger.info("memory_deleted", memory_id=memory_id, user_id=user_id)
            return True
        return False

    def evaluate_memory_candidate(
        self,
        content: str,
        user_query: str,
        response: str,
    ) -> Optional[dict]:
        """
        Evaluate whether an interaction should be stored as memory.
        Returns memory candidate dict or None.
        """
        # Simple heuristic-based extraction
        indicators = {
            "contains_insight": any(w in response.lower() for w in [
                "highest", "lowest", "increased", "decreased", "growth",
                "decline", "trend", "pattern", "notable", "significant",
            ]),
            "contains_comparison": any(w in response.lower() for w in [
                "compared", "versus", "more than", "less than", "outperformed",
            ]),
            "mentions_region": any(r in response for r in ["North", "South", "East", "West"]),
            "mentions_segment": any(s in response for s in ["Enterprise", "Mid-Market", "Small Business", "Startup"]),
            "is_data_result": "$" in response or "%" in response,
        }

        score = sum(indicators.values()) / len(indicators)

        if score >= 0.4:
            # Extract entities
            entities = []
            for region in ["North", "South", "East", "West"]:
                if region in response:
                    entities.append(region)
            for segment in ["Enterprise", "Mid-Market", "Small Business", "Startup"]:
                if segment in response:
                    entities.append(segment)

            return {
                "content": f"User asked: {user_query}\nFinding: {response[:500]}",
                "summary": response[:200],
                "memory_type": "insight" if indicators["contains_insight"] else "analysis",
                "entities": entities,
                "importance_score": round(min(score + 0.2, 1.0), 2),
                "confidence": 0.8,
            }

        return None
