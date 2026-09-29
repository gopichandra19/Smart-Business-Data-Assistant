"""Pydantic contracts - API request/response models and shared types."""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


# ─── Auth ──────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool


# ─── Chat ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[int] = None


class EvidenceItem(BaseModel):
    type: str  # database, knowledge, memory, calculation
    source: str
    detail: Optional[str] = None


class ToolCallRecord(BaseModel):
    tool: str
    input_summary: str
    output_summary: str
    execution_time_ms: float
    status: str


class VisualizationSpec(BaseModel):
    type: str  # bar, line, pie, table
    title: str
    x: Optional[str] = None
    y: Optional[str] = None
    data: Optional[list[dict]] = None
    columns: Optional[list[str]] = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    intent: str = "UNKNOWN"
    evidence: list[EvidenceItem] = []
    knowledge: list[dict] = []
    memory: list[dict] = []
    tool_calls: list[ToolCallRecord] = []
    visualizations: list[VisualizationSpec] = []
    suggested_questions: list[str] = []
    request_id: str = ""


# ─── Conversations ─────────────────────────────────────────────

class ConversationSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    metadata_json: Optional[dict] = None
    created_at: datetime


class ConversationDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: list[MessageResponse] = []


# ─── Dashboard ─────────────────────────────────────────────────

class DashboardCard(BaseModel):
    label: str
    value: Any
    change: Optional[float] = None
    icon: Optional[str] = None


class DashboardResponse(BaseModel):
    cards: list[DashboardCard] = []
    revenue_by_region: list[dict] = []
    revenue_by_month: list[dict] = []
    top_customers: list[dict] = []
    sales_by_product: list[dict] = []
    recent_insights: list[dict] = []


# ─── Data Sources ──────────────────────────────────────────────

class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    status: str
    record_count: int
    table_count: int
    last_sync: Optional[datetime] = None
    created_at: datetime


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    connection_config: dict = {}


# ─── Knowledge ─────────────────────────────────────────────────

class KnowledgeDocResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    business_domain: Optional[str] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    version: int
    created_at: datetime


class KnowledgeDocCreate(BaseModel):
    title: str
    content: str
    category: str
    business_domain: Optional[str] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None


# ─── Memory ────────────────────────────────────────────────────

class MemoryResponse(BaseModel):
    id: int
    memory_type: str
    content: str
    summary: Optional[str] = None
    importance_score: float
    confidence: float
    created_at: datetime
    last_accessed_at: datetime


# ─── Audit ─────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    request_id: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    timestamp: datetime
    action: str
    tool: Optional[str] = None
    query: Optional[str] = None
    intent: Optional[str] = None
    status: str
    latency_ms: Optional[float] = None
    metadata_json: Optional[dict] = None


# ─── Insights ──────────────────────────────────────────────────

class InsightResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str  # info, warning, critical
    category: str
    data: Optional[dict] = None
    detected_at: datetime


# ─── Agent Internal ────────────────────────────────────────────

class IntentType(str, Enum):
    DATA_LOOKUP = "DATA_LOOKUP"
    AGGREGATION = "AGGREGATION"
    COMPARISON = "COMPARISON"
    TREND_ANALYSIS = "TREND_ANALYSIS"
    ROOT_CAUSE_EXPLORATION = "ROOT_CAUSE_EXPLORATION"
    HISTORICAL_COMPARISON = "HISTORICAL_COMPARISON"
    MEMORY_RECALL = "MEMORY_RECALL"
    DEFINITION = "DEFINITION"
    FOLLOW_UP = "FOLLOW_UP"
    UNKNOWN = "UNKNOWN"


class QueryPlan(BaseModel):
    intent: str
    metric: Optional[str] = None
    dimensions: list[str] = []
    filters: dict = {}
    time_range: Optional[str] = None
    aggregation: Optional[str] = None
    sort: Optional[str] = None
    limit: Optional[int] = None
    tables: list[str] = []
    reasoning: str = ""


class AssistantState(BaseModel):
    """Complete state for the agent orchestrator."""
    user_query: str = ""
    user_id: int = 0
    user_role: str = "employee"
    conversation_id: int = 0
    request_id: str = ""
    intent: str = "UNKNOWN"
    business_terms: list[str] = []
    retrieved_knowledge: list[dict] = []
    retrieved_memory: list[dict] = []
    query_plan: Optional[QueryPlan] = None
    selected_tools: list[str] = []
    sql_query: Optional[str] = None
    tool_results: list[dict] = []
    analysis: str = ""
    citations: list[EvidenceItem] = []
    response: str = ""
    visualizations: list[VisualizationSpec] = []
    suggested_questions: list[str] = []
    memories_to_store: list[dict] = []
    errors: list[str] = []
    tool_call_records: list[ToolCallRecord] = []
    iteration_count: int = 0
    max_iterations: int = 5
