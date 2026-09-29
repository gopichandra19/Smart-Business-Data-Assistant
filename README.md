# Smart Business Data Assistant

A production-oriented prototype of a **Memory-Driven Smart Business Data Assistant** that combines persistent memory, RAG, MCP-controlled tools, LLM reasoning, and structured business data querying to deliver evidence-backed conversational business intelligence.

## Architecture

```
Business Data → Persistent Memory → RAG Knowledge → MCP Tools → LLM Agent → Evidence-Backed Answers
```

## Features

- **Natural-language business queries** with evidence-backed responses
- **RAG-based business knowledge** retrieval (definitions, schemas, KPIs, rules)
- **Persistent analytical memory** (Hindsight-style) with semantic search and ranking
- **MCP-controlled tool access** with audit logging
- **SQL generation and validation** (read-only, with role-based column restrictions)
- **Role-based access control** (Employee, Manager, Analyst, Admin)
- **Field-level data restrictions** per role
- **Prompt injection defenses** and SQL injection prevention
- **Complete audit trail** for all AI interactions
- **Rule-based proactive insights**
- **Multi-turn conversation** with follow-up suggestions
- **Interactive dashboard** with charts and KPIs
- **Human approval architecture** for sensitive operations

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite (PostgreSQL-ready) |
| AI/Agent | OpenAI/Anthropic (abstracted), structured output |
| RAG | sentence-transformers, FAISS-compatible vector store |
| Frontend | React, TypeScript, Vite, Tailwind CSS, Recharts |
| Auth | JWT, bcrypt |

## Quick Start

### 1. Clone & Install Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env and add your LLM_API_KEY
```

### 2. Start Backend

```bash
python -m uvicorn apps.api.main:app --reload --port 8000
```

The backend will:
- Initialize the SQLite database
- Seed 10,000+ demo business records
- Create 4 demo users
- Index 30+ business knowledge documents
- Start the API on http://localhost:8000

### 3. Start Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

### 4. Login

Use any demo account:
- `analyst@example.local` / `analyst123` (recommended)
- `admin@example.local` / `admin123`
- `manager@example.local` / `manager123`
- `employee@example.local` / `employee123`

## Demo Scenarios

1. **Simple Aggregation**: "Which region generated the highest revenue last quarter?"
2. **Follow-up Reasoning**: "Why did South perform better?"
3. **Memory Recall**: "What did we discover about South previously?"
4. **Trend Analysis**: "Show South-region revenue for the last 12 months"
5. **Segmentation**: "Which customer segment contributed most to South revenue?"
6. **Definition Lookup**: "What does active customer mean?"
7. **Access Control**: Login as employee, try to query salary data → denied

## Running Tests

```bash
python -m pytest tests/ -v
```

## Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Description | Default |
|----------|------------|---------|
| `LLM_API_KEY` | Your LLM provider API key | (required) |
| `LLM_PROVIDER` | openai, anthropic, local | openai |
| `LLM_MODEL` | Model name | gpt-4o-mini |
| `DATABASE_URL` | Database connection string | sqlite:///./data/business.db |
| `MAX_QUERY_ROWS` | Maximum rows per query | 1000 |

## Security Notes

- SQL queries are **read-only** (SELECT only), enforced in code
- Dangerous keywords blocked: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE
- Field-level access control per role
- Prompt injection patterns filtered from all retrieved data
- All tool executions logged to audit trail
- JWT-based authentication
- CORS configured

## Prototype Limitations

- Single-tenant prototype
- SQLite (not PostgreSQL in default config)
- Simplified memory ranking (heuristic-based)
- Basic embedding model (MiniLM)
- Development authentication (seeded passwords)
- Rule-based insights (not ML)
- Read-only tool execution only

## Project Structure

```
├── apps/api/          # FastAPI application
├── apps/frontend/     # React frontend
├── services/          # Domain services (agent, rag, memory, mcp, auth, audit)
├── packages/          # Shared packages (config, database, llm, security, observability)
├── data/demo/         # Demo data generator
├── tests/             # Unit, security, integration tests
├── docs/              # Architecture documentation
├── docker/            # Dockerfiles
└── docker-compose.yml
```
