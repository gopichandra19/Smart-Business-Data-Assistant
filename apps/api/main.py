"""
Smart Business Data Assistant - FastAPI Application
Main entry point for the API server.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from jose import JWTError, jwt
from packages.security.password import verify_password, hash_password

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.database.connection import get_db, init_db, get_engine
from packages.database.models import (
    User, Conversation, Message, KnowledgeDocument,
    Memory, AuditLog, DataSource, SavedAnalysis,
    Customer, Order, Transaction, Product, Salesperson, Campaign,
)
from packages.contracts.schemas import (
    LoginRequest, LoginResponse, UserResponse,
    ChatRequest, ChatResponse, EvidenceItem, ToolCallRecord, VisualizationSpec,
    ConversationSummary, ConversationDetail, MessageResponse,
    DashboardResponse, DashboardCard,
    DataSourceResponse, DataSourceCreate,
    KnowledgeDocResponse, KnowledgeDocCreate,
    MemoryResponse, AuditLogResponse, InsightResponse,
)
from packages.config import get_settings
from packages.observability.logging import (
    setup_logging, get_logger, generate_correlation_id,
    correlation_id_var, user_id_var,
)
from services.agent.orchestrator import AgentOrchestrator
from services.rag.service import RAGService
from services.memory.service import MemoryService
from services.authorization.service import AuthorizationService

logger = get_logger("api")
settings = get_settings()
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown."""
    setup_logging(settings.log_level)
    logger.info("application_starting", env=settings.app_env)

    # Initialize database
    os.makedirs("data", exist_ok=True)
    init_db()

    # Seed demo data if needed
    from data.demo.seed import generate_demo_data
    try:
        generate_demo_data()
    except Exception as e:
        logger.warning("demo_data_seed_error", error=str(e))

    # Index knowledge for RAG
    from packages.database.connection import get_db_session
    with get_db_session() as db:
        rag = RAGService(db)
        count = rag.index_knowledge()
        logger.info("knowledge_indexed_at_startup", count=count)

    logger.info("application_started")
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="Smart Business Data Assistant",
    description="Memory-driven AI business intelligence assistant with RAG, MCP, and RBAC",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth Helpers ──────────────────────────────────────────────

def create_access_token(user_id: int, email: str, role: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and verify the current user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = int(payload.get("sub", 0))
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid or inactive user")

        # Set context vars for logging
        correlation_id_var.set(generate_correlation_id())
        user_id_var.set(str(user_id))

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*roles: str):
    """Dependency factory to require specific roles."""
    def check(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: requires role {roles}",
            )
        return user
    return check


# ─── Health ────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")


# ─── Auth ──────────────────────────────────────────────────────

@app.post("/api/v1/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(user.id, user.email, user.role)

    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, email=user.email, name=user.name,
            role=user.role, is_active=user.is_active,
        ),
    )


@app.get("/api/v1/auth/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id, email=user.email, name=user.name,
        role=user.role, is_active=user.is_active,
    )


# ─── Dashboard ─────────────────────────────────────────────────

@app.get("/api/v1/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # KPI Cards
    total_customers = db.query(func.count(Customer.customer_id)).scalar() or 0
    total_orders = db.query(func.count(Order.order_id)).scalar() or 0
    total_revenue = db.query(func.sum(Transaction.revenue)).scalar() or 0
    total_knowledge = db.query(func.count(KnowledgeDocument.id)).scalar() or 0
    total_memories = db.query(func.count(Memory.id)).filter(Memory.user_id == user.id).scalar() or 0
    queries_today = db.query(func.count(AuditLog.id)).filter(
        AuditLog.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0),
        AuditLog.user_id == user.id,
    ).scalar() or 0
    data_sources = db.query(func.count(DataSource.id)).scalar() or 0

    cards = [
        DashboardCard(label="Connected Data Sources", value=data_sources, icon="database"),
        DashboardCard(label="Total Customers", value=total_customers, icon="users"),
        DashboardCard(label="Total Orders", value=total_orders, icon="shopping-cart"),
        DashboardCard(label="Total Revenue", value=f"${total_revenue:,.0f}", icon="dollar-sign"),
        DashboardCard(label="Knowledge Documents", value=total_knowledge, icon="book"),
        DashboardCard(label="Stored Memories", value=total_memories, icon="brain"),
        DashboardCard(label="Queries Today", value=queries_today, icon="search"),
    ]

    # Revenue by Region
    rev_by_region = db.execute(text("""
        SELECT c.region, ROUND(SUM(t.revenue), 2) as total_revenue
        FROM transactions t
        JOIN orders o ON t.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.region ORDER BY total_revenue DESC
    """)).fetchall()
    revenue_by_region = [{"region": r[0], "revenue": r[1]} for r in rev_by_region]

    # Revenue by Month (last 12 months)
    rev_by_month = db.execute(text("""
        SELECT strftime('%Y-%m', t.transaction_date) as month, ROUND(SUM(t.revenue), 2) as revenue
        FROM transactions t
        WHERE t.transaction_date >= date('now', '-12 months')
        GROUP BY month ORDER BY month
    """)).fetchall()
    revenue_by_month = [{"month": r[0], "revenue": r[1]} for r in rev_by_month]

    # Top Customers
    top_custs = db.execute(text("""
        SELECT c.customer_name, c.segment, ROUND(SUM(t.revenue), 2) as revenue
        FROM transactions t
        JOIN orders o ON t.order_id = o.order_id
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.customer_id ORDER BY revenue DESC LIMIT 10
    """)).fetchall()
    top_customers = [{"name": r[0], "segment": r[1], "revenue": r[2]} for r in top_custs]

    # Sales by Product Category
    sales_by_product = db.execute(text("""
        SELECT p.category, ROUND(SUM(t.revenue), 2) as revenue, COUNT(DISTINCT o.order_id) as orders
        FROM transactions t
        JOIN orders o ON t.order_id = o.order_id
        JOIN products p ON o.product_id = p.product_id
        GROUP BY p.category ORDER BY revenue DESC
    """)).fetchall()
    sales_product = [{"category": r[0], "revenue": r[1], "orders": r[2]} for r in sales_by_product]

    # Recent insights (rule-based)
    insights = _detect_insights(db)

    return DashboardResponse(
        cards=cards,
        revenue_by_region=revenue_by_region,
        revenue_by_month=revenue_by_month,
        top_customers=top_customers,
        sales_by_product=sales_product,
        recent_insights=[{"title": i.title, "description": i.description, "severity": i.severity} for i in insights[:5]],
    )


# ─── Chat ──────────────────────────────────────────────────────

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Main chat endpoint - processes business questions through the agent pipeline."""
    request_id = generate_correlation_id()
    correlation_id_var.set(request_id)

    # Get or create conversation
    if req.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == req.conversation_id,
            Conversation.user_id == user.id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(
            user_id=user.id,
            title=req.message[:80] + ("..." if len(req.message) > 80 else ""),
        )
        db.add(conv)
        db.flush()

    # Store user message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.flush()

    # Get conversation history
    history_msgs = db.query(Message).filter(
        Message.conversation_id == conv.id,
    ).order_by(Message.created_at).all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs[-10:]]

    # Run agent pipeline
    agent = AgentOrchestrator(db)
    state = await agent.process_query(
        query=req.message,
        user_id=user.id,
        user_role=user.role,
        conversation_id=conv.id,
        conversation_history=history,
    )

    # Store assistant response
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=state.response,
        metadata_json={
            "intent": state.intent,
            "request_id": state.request_id,
            "sql_query": state.sql_query,
            "knowledge_count": len(state.retrieved_knowledge),
            "memory_count": len(state.retrieved_memory),
            "tool_calls": len(state.tool_call_records),
        },
    )
    db.add(assistant_msg)
    db.flush()

    # Update conversation
    conv.updated_at = datetime.utcnow()

    # Audit log
    audit = AuditLog(
        request_id=request_id,
        user_id=user.id,
        conversation_id=conv.id,
        action="chat",
        intent=state.intent,
        query=state.sql_query,
        status="success" if not state.errors else "partial",
        metadata_json={
            "question": req.message[:500],
            "knowledge_retrieved": len(state.retrieved_knowledge),
            "memories_retrieved": len(state.retrieved_memory),
            "tool_calls": len(state.tool_call_records),
            "errors": state.errors[:3] if state.errors else [],
        },
    )
    db.add(audit)
    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        answer=state.response,
        intent=state.intent,
        evidence=state.citations,
        knowledge=[
            {"title": k.get("title", ""), "category": k.get("category", ""), "similarity": k.get("similarity", 0)}
            for k in state.retrieved_knowledge[:5]
        ],
        memory=[
            {"summary": m.get("summary", ""), "type": m.get("memory_type", ""), "score": m.get("score", 0)}
            for m in state.retrieved_memory[:3]
        ],
        tool_calls=state.tool_call_records,
        visualizations=state.visualizations,
        suggested_questions=state.suggested_questions,
        request_id=request_id,
    )


# ─── Conversations ─────────────────────────────────────────────

@app.get("/api/v1/conversations")
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    convs = db.query(Conversation).filter(
        Conversation.user_id == user.id,
    ).order_by(Conversation.updated_at.desc()).limit(50).all()

    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=db.query(func.count(Message.id)).filter(Message.conversation_id == c.id).scalar() or 0,
        )
        for c in convs
    ]


@app.get("/api/v1/conversations/{conversation_id}")
def get_conversation(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
    ).order_by(Message.created_at).all()

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        messages=[
            MessageResponse(
                id=m.id, role=m.role, content=m.content,
                metadata_json=m.metadata_json, created_at=m.created_at,
            )
            for m in messages
        ],
    )


# ─── Data Sources ──────────────────────────────────────────────

@app.get("/api/v1/data-sources")
def list_data_sources(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sources = db.query(DataSource).all()
    return [
        DataSourceResponse(
            id=s.id, name=s.name, source_type=s.source_type,
            status=s.status, record_count=s.record_count,
            table_count=s.table_count, last_sync=s.last_sync, created_at=s.created_at,
        )
        for s in sources
    ]


@app.post("/api/v1/data-sources")
def create_data_source(
    req: DataSourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    ds = DataSource(
        name=req.name, source_type=req.source_type,
        connection_config=req.connection_config,
    )
    db.add(ds)
    db.commit()
    return {"id": ds.id, "name": ds.name, "status": "created"}


# ─── Knowledge ─────────────────────────────────────────────────

@app.get("/api/v1/knowledge")
def list_knowledge(
    category: Optional[str] = None,
    domain: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rag = RAGService(db)
    docs = rag.get_all_documents(category=category, domain=domain, search_text=search)
    return [
        KnowledgeDocResponse(
            id=d.id, title=d.title, content=d.content, category=d.category,
            business_domain=d.business_domain, table_name=d.table_name,
            column_name=d.column_name, version=d.version, created_at=d.created_at,
        )
        for d in docs
    ]


@app.post("/api/v1/knowledge")
def add_knowledge(
    req: KnowledgeDocCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("analyst", "admin")),
):
    rag = RAGService(db)
    doc = rag.add_document(
        title=req.title, content=req.content, category=req.category,
        business_domain=req.business_domain, table_name=req.table_name,
        column_name=req.column_name,
    )
    db.commit()
    return {"id": doc.id, "title": doc.title, "status": "created"}


# ─── Memory ────────────────────────────────────────────────────

@app.get("/api/v1/memories")
def list_memories(
    memory_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    mem_service = MemoryService(db)
    memories = mem_service.get_user_memories(user.id, memory_type=memory_type)
    return [
        MemoryResponse(
            id=m.id, memory_type=m.memory_type, content=m.content,
            summary=m.summary, importance_score=m.importance_score,
            confidence=m.confidence, created_at=m.created_at,
            last_accessed_at=m.last_accessed_at,
        )
        for m in memories
    ]


@app.delete("/api/v1/memories/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    mem_service = MemoryService(db)
    deleted = mem_service.delete_memory(memory_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.commit()
    return {"status": "deleted"}


# ─── Audit ─────────────────────────────────────────────────────

@app.get("/api/v1/audit")
def list_audit_logs(
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("analyst", "admin")),
):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        AuditLogResponse(
            id=l.id, request_id=l.request_id, user_id=l.user_id,
            conversation_id=l.conversation_id, timestamp=l.timestamp,
            action=l.action, tool=l.tool, query=l.query, intent=l.intent,
            status=l.status, latency_ms=l.latency_ms, metadata_json=l.metadata_json,
        )
        for l in logs
    ]


# ─── Insights ──────────────────────────────────────────────────

@app.get("/api/v1/insights")
def get_insights(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    insights = _detect_insights(db)
    return [
        InsightResponse(
            id=i.id, title=i.title, description=i.description,
            severity=i.severity, category=i.category,
            data=i.data, detected_at=i.detected_at,
        )
        for i in insights
    ]


def _detect_insights(db: Session) -> list:
    """Rule-based prototype insight detection."""
    from packages.contracts.schemas import InsightResponse
    insights = []

    try:
        # Insight 1: Regional revenue comparison
        regions = db.execute(text("""
            SELECT c.region, ROUND(SUM(t.revenue), 2) as revenue
            FROM transactions t
            JOIN orders o ON t.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE t.transaction_date >= date('now', '-3 months')
            GROUP BY c.region ORDER BY revenue DESC
        """)).fetchall()

        if len(regions) >= 2:
            top = regions[0]
            bottom = regions[-1]
            if top[1] > 0 and bottom[1] > 0:
                ratio = top[1] / bottom[1]
                if ratio > 1.5:
                    insights.append(InsightResponse(
                        id="insight-regional-gap",
                        title=f"{top[0]} Region Revenue Lead",
                        description=f"Rule-based prototype insight: {top[0]} region generated ${top[1]:,.0f} in the last 3 months, {ratio:.1f}x more than {bottom[0]} (${bottom[1]:,.0f}).",
                        severity="info",
                        category="regional_performance",
                        data={"top_region": top[0], "top_revenue": top[1], "bottom_region": bottom[0], "bottom_revenue": bottom[1]},
                        detected_at=datetime.utcnow(),
                    ))

        # Insight 2: Segment concentration
        segments = db.execute(text("""
            SELECT c.segment, ROUND(SUM(t.revenue), 2) as revenue
            FROM transactions t
            JOIN orders o ON t.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE t.transaction_date >= date('now', '-3 months')
            GROUP BY c.segment ORDER BY revenue DESC
        """)).fetchall()

        if segments:
            total = sum(s[1] for s in segments)
            if total > 0:
                top_pct = (segments[0][1] / total) * 100
                if top_pct > 40:
                    insights.append(InsightResponse(
                        id="insight-segment-concentration",
                        title=f"{segments[0][0]} Segment Concentration",
                        description=f"Rule-based prototype insight: {segments[0][0]} customers represent {top_pct:.0f}% of recent revenue, indicating segment concentration.",
                        severity="warning" if top_pct > 60 else "info",
                        category="segment_analysis",
                        data={"segment": segments[0][0], "percentage": round(top_pct, 1)},
                        detected_at=datetime.utcnow(),
                    ))

        # Insight 3: Product category performance
        categories = db.execute(text("""
            SELECT p.category, COUNT(DISTINCT o.order_id) as order_count
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.order_date >= date('now', '-1 month')
            GROUP BY p.category ORDER BY order_count DESC
        """)).fetchall()

        if categories:
            insights.append(InsightResponse(
                id="insight-product-demand",
                title=f"Top Product Category: {categories[0][0]}",
                description=f"Rule-based prototype insight: {categories[0][0]} leads with {categories[0][1]} orders in the last month.",
                severity="info",
                category="product_performance",
                data={"categories": [{"category": c[0], "orders": c[1]} for c in categories]},
                detected_at=datetime.utcnow(),
            ))

    except Exception as e:
        logger.warning("insight_detection_error", error=str(e))

    return insights


# ─── Settings ──────────────────────────────────────────────────

@app.get("/api/v1/settings")
def get_settings_api(user: User = Depends(require_role("admin"))):
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "vector_store": settings.vector_store,
        "rag_top_k": settings.rag_top_k,
        "memory_enabled": settings.memory_enabled,
        "memory_max_results": settings.memory_max_results,
        "max_query_rows": settings.max_query_rows,
        "sql_timeout_seconds": settings.sql_timeout_seconds,
        "log_level": settings.log_level,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
