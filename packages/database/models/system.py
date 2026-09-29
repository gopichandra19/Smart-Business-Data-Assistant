"""Database models for system entities - users, conversations, knowledge, memory, audit."""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from packages.database.connection import Base
from datetime import datetime
import enum


# ─── User & Auth ───────────────────────────────────────────────

class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ANALYST = "analyst"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    password_hash = Column(String(300), nullable=False)
    role = Column(String(20), default=UserRole.EMPLOYEE.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")
    memories = relationship("Memory", back_populates="user")


# ─── Conversations ─────────────────────────────────────────────

class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM_EVENT = "system_event"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(300), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# ─── Knowledge / RAG ──────────────────────────────────────────

class KnowledgeCategory(str, enum.Enum):
    SCHEMA = "schema"
    COLUMN_DEFINITION = "column_definition"
    BUSINESS_RULE = "business_rule"
    KPI = "kpi"
    RELATIONSHIP = "relationship"
    GLOSSARY = "glossary"
    POLICY = "policy"
    EXAMPLE = "example"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(30), nullable=False, index=True)
    business_domain = Column(String(100))
    table_name = Column(String(100), index=True)
    column_name = Column(String(100))
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("KnowledgeChunk", back_populates="document")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("KnowledgeDocument", back_populates="chunks")


# ─── Memory ────────────────────────────────────────────────────

class MemoryType(str, enum.Enum):
    CONVERSATION = "conversation"
    INSIGHT = "insight"
    USER_PREFERENCE = "user_preference"
    ANALYSIS = "analysis"
    ENTITY = "entity"
    BUSINESS_CONTEXT = "business_context"


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    memory_type = Column(String(30), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    entities_json = Column(JSON, default=list)
    importance_score = Column(Float, default=0.5)
    confidence = Column(Float, default=0.8)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default=dict)

    user = relationship("User", back_populates="memories")


# ─── Audit ─────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    conversation_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(100), nullable=False)
    tool = Column(String(100))
    query = Column(Text)
    intent = Column(String(50))
    status = Column(String(20), nullable=False)
    latency_ms = Column(Float)
    metadata_json = Column(JSON, default=dict)


# ─── Data Sources ──────────────────────────────────────────────

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)
    connection_config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    record_count = Column(Integer, default=0)
    table_count = Column(Integer, default=0)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Saved Analyses ───────────────────────────────────────────

class SavedAnalysis(Base):
    __tablename__ = "saved_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    question = Column(Text, nullable=False)
    query_plan_json = Column(JSON)
    sql_query = Column(Text)
    result_summary = Column(Text)
    charts_json = Column(JSON)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Approval ──────────────────────────────────────────────────

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    payload_json = Column(JSON, default=dict)
    reason = Column(Text)
    status = Column(String(20), default=ApprovalStatus.PENDING.value)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    decision_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
