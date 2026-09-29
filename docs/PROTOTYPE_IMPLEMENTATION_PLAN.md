# Smart Business Data Assistant — Prototype Implementation Plan

## 1. Current Repository Status

**Status**: Empty workspace — fresh greenfield build.
**Date**: 2026-09-29

---

## 2. Proposed Architecture

Frontend (React/Vite/TS/Tailwind) → API Gateway (FastAPI) → Application Services → Agent Orchestrator → MCP/RAG/Memory Layers → LLM/Data/Auth Infrastructure

---

## 3. Directory Structure

```
smart-business-assistant/
├── apps/
│   ├── frontend/          # React + Vite + TypeScript + Tailwind
│   └── api/               # FastAPI application entry point
├── services/
│   ├── agent/             # Agent orchestrator, intent, planner
│   ├── rag/               # Knowledge ingestion, retrieval, embeddings
│   ├── memory/            # Persistent memory store, ranking, extraction
│   ├── mcp/               # Tool registry, execution, schemas
│   ├── data_query/        # SQL generation, validation, execution
│   ├── authorization/     # RBAC, field access, approval
│   └── audit/             # Audit logging, observability
├── packages/
│   ├── contracts/         # Pydantic models, shared types
│   ├── llm/               # LLM provider abstraction
│   ├── database/          # DB connection, session, base models
│   ├── observability/     # Structured logging, metrics
│   └── security/          # Input validation, prompt defense, SQL safety
├── data/
│   ├── demo/              # Demo data generation scripts
│   └── knowledge/         # Business knowledge documents
├── migrations/            # Alembic migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── e2e/
├── scripts/               # Setup, seed, utility scripts
├── docs/
├── docker/
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 4. Database Schema

### Business: customers, orders, transactions, products, salespeople, campaigns
### System: users, conversations, messages, knowledge_documents, knowledge_chunks, memories, audit_logs, data_sources, saved_analyses, approval_requests

---

## 5. Milestones

| Phase | Scope |
|-------|-------|
| 1 | Foundation: repo, FastAPI, DB, migrations, React shell |
| 2 | Business Data: schema, 10K+ demo records, connectors |
| 3 | Knowledge/RAG: ingestion, embeddings, retrieval |
| 4 | Memory: models, extraction, ranking, retrieval |
| 5 | MCP: tool registry, schemas, permissions, audit |
| 6 | LLM Agent: intent, planning, SQL gen, analysis |
| 7 | Chat UI: conversation, evidence, charts |
| 8 | Enterprise: auth, RBAC, field restrictions, audit |
| 9 | Testing: unit, integration, security, E2E |
| 10 | Verification: demo scenarios, acceptance report |

---

## 6. Design Decisions

1. SQLite for prototype, PostgreSQL-ready via SQLAlchemy
2. FAISS for vectors, replaceable via VectorStore interface
3. sentence-transformers for local embeddings
4. JWT for auth
5. Deterministic demo data with seeded random
6. Clean state machine for agent (no unbounded loops)
7. Recharts for frontend charting
