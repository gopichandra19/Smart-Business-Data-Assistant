"""MCP Tool Layer - controlled tool access with audit logging."""

import time
from datetime import datetime, date, timedelta
from typing import Any, Callable, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from packages.database.models import AuditLog
from packages.security.sql_validator import validate_sql, ALLOWED_TABLES
from packages.observability.logging import get_logger, correlation_id_var

logger = get_logger("mcp")


class ToolSchema(BaseModel):
    """Schema for an MCP tool."""
    name: str
    description: str
    input_schema: dict = {}
    output_schema: dict = {}
    permissions: list[str] = ["employee", "manager", "analyst", "admin"]
    timeout_seconds: int = 30
    requires_approval: bool = False
    audit_policy: str = "always"  # always, on_error, never


class ToolResult(BaseModel):
    """Result from executing an MCP tool."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0


class MCPToolRegistry:
    """Registry for controlled MCP tools."""

    def __init__(self, db: Session):
        self.db = db
        self._tools: dict[str, tuple[ToolSchema, Callable]] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register all built-in business tools."""

        # ── query_business_data ────────────────────────
        self.register(
            ToolSchema(
                name="query_business_data",
                description="Execute a read-only SQL query against business data tables. Returns columns and rows.",
                input_schema={"query": "string", "reason": "string"},
                output_schema={"columns": "list", "rows": "list", "row_count": "int"},
                permissions=["analyst", "admin", "manager", "employee"],
            ),
            self._execute_query,
        )

        # ── get_database_schema ────────────────────────
        self.register(
            ToolSchema(
                name="get_database_schema",
                description="Get the list of available business data tables and their columns.",
                permissions=["analyst", "admin"],
            ),
            self._get_schema,
        )

        # ── get_table_schema ──────────────────────────
        self.register(
            ToolSchema(
                name="get_table_schema",
                description="Get detailed schema for a specific table.",
                input_schema={"table_name": "string"},
                permissions=["analyst", "admin", "manager"],
            ),
            self._get_table_schema,
        )

        # ── search_business_knowledge ──────────────────
        self.register(
            ToolSchema(
                name="search_business_knowledge",
                description="Search business knowledge base for definitions, rules, KPIs, and schema information.",
                input_schema={"query": "string", "category": "string|null"},
                permissions=["employee", "manager", "analyst", "admin"],
            ),
            self._search_knowledge,
        )

        # ── search_memory ─────────────────────────────
        self.register(
            ToolSchema(
                name="search_memory",
                description="Search previous analyses and insights stored in memory.",
                input_schema={"query": "string"},
                permissions=["employee", "manager", "analyst", "admin"],
            ),
            self._search_memory,
        )

        # ── get_time_period ───────────────────────────
        self.register(
            ToolSchema(
                name="get_time_period",
                description="Resolve a natural-language time period to concrete date boundaries.",
                input_schema={"period": "string"},
                permissions=["employee", "manager", "analyst", "admin"],
            ),
            self._get_time_period,
        )

        # ── create_chart_spec ─────────────────────────
        self.register(
            ToolSchema(
                name="create_chart_spec",
                description="Create a visualization specification for rendering charts.",
                input_schema={"type": "string", "title": "string", "x": "string", "y": "string", "data": "list"},
                permissions=["employee", "manager", "analyst", "admin"],
            ),
            self._create_chart_spec,
        )

    def register(self, schema: ToolSchema, handler: Callable):
        """Register a new tool."""
        self._tools[schema.name] = (schema, handler)
        logger.info("tool_registered", tool=schema.name)

    def get_tool_schemas(self, user_role: str = "employee") -> list[dict]:
        """Get schemas of tools accessible to the user's role."""
        schemas = []
        for name, (schema, _) in self._tools.items():
            if user_role in schema.permissions:
                schemas.append({
                    "name": schema.name,
                    "description": schema.description,
                    "input_schema": schema.input_schema,
                })
        return schemas

    def execute(
        self,
        tool_name: str,
        inputs: dict,
        user_id: int,
        user_role: str,
        conversation_id: Optional[int] = None,
        request_id: str = "",
    ) -> ToolResult:
        """Execute a registered tool with audit logging."""
        if tool_name not in self._tools:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        schema, handler = self._tools[tool_name]

        # Check permissions
        if user_role not in schema.permissions:
            self._audit_log(
                request_id, user_id, conversation_id,
                f"tool_denied:{tool_name}", tool_name,
                str(inputs)[:500], "denied", 0,
            )
            return ToolResult(
                success=False,
                error=f"Access denied: role '{user_role}' cannot use tool '{tool_name}'",
            )

        # Execute with timing
        start = time.perf_counter()
        try:
            result = handler(inputs, user_id=user_id, user_role=user_role)
            elapsed = (time.perf_counter() - start) * 1000

            self._audit_log(
                request_id, user_id, conversation_id,
                f"tool_call:{tool_name}", tool_name,
                str(inputs)[:500], "success", elapsed,
            )

            return ToolResult(success=True, data=result, execution_time_ms=round(elapsed, 2))

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("tool_execution_error", tool=tool_name, error=str(e))

            self._audit_log(
                request_id, user_id, conversation_id,
                f"tool_error:{tool_name}", tool_name,
                str(inputs)[:500], "error", elapsed,
                metadata={"error": str(e)},
            )

            return ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)[:200]}",
                execution_time_ms=round(elapsed, 2),
            )

    def _audit_log(
        self, request_id, user_id, conversation_id,
        action, tool, query, status, latency_ms, metadata=None,
    ):
        """Write audit log entry."""
        log = AuditLog(
            request_id=request_id or "",
            user_id=user_id,
            conversation_id=conversation_id,
            action=action,
            tool=tool,
            query=query,
            status=status,
            latency_ms=round(latency_ms, 2),
            metadata_json=metadata or {},
        )
        self.db.add(log)
        try:
            self.db.flush()
        except Exception:
            pass  # Don't fail main operation if audit write fails

    # ── Tool Handlers ──────────────────────────────────

    def _execute_query(self, inputs: dict, **kwargs) -> dict:
        """Execute a validated read-only SQL query."""
        sql = inputs.get("query", "")
        user_role = kwargs.get("user_role", "employee")
        max_rows = 1000

        # Validate SQL
        validation = validate_sql(sql, user_role=user_role, max_rows=max_rows)
        if not validation.is_valid:
            return {"error": "; ".join(validation.errors), "columns": [], "rows": [], "row_count": 0}

        try:
            result = self.db.execute(text(validation.sql))
            columns = list(result.keys()) if result.returns_rows else []
            rows = [dict(zip(columns, row)) for row in result.fetchall()] if columns else []

            return {
                "columns": columns,
                "rows": rows[:max_rows],
                "row_count": len(rows),
            }
        except Exception as e:
            return {"error": str(e)[:300], "columns": [], "rows": [], "row_count": 0}

    def _get_schema(self, inputs: dict, **kwargs) -> dict:
        """Get database schema information."""
        schema = {}
        for table in ALLOWED_TABLES:
            try:
                result = self.db.execute(text(f"PRAGMA table_info({table})"))
                columns = [{"name": row[1], "type": row[2], "nullable": not row[3]} for row in result.fetchall()]
                schema[table] = columns
            except Exception:
                schema[table] = []
        return {"tables": schema}

    def _get_table_schema(self, inputs: dict, **kwargs) -> dict:
        """Get schema for specific table."""
        table = inputs.get("table_name", "")
        if table not in ALLOWED_TABLES:
            return {"error": f"Table '{table}' not accessible"}
        try:
            result = self.db.execute(text(f"PRAGMA table_info({table})"))
            columns = [{"name": row[1], "type": row[2], "nullable": not row[3]} for row in result.fetchall()]

            count_result = self.db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = count_result.scalar()

            return {"table": table, "columns": columns, "row_count": count}
        except Exception as e:
            return {"error": str(e)[:200]}

    def _search_knowledge(self, inputs: dict, **kwargs) -> dict:
        """Search business knowledge base."""
        from services.rag.service import RAGService
        rag = RAGService(self.db)
        results = rag.search_knowledge(
            query=inputs.get("query", ""),
            category=inputs.get("category"),
        )
        return {"results": results}

    def _search_memory(self, inputs: dict, **kwargs) -> dict:
        """Search persistent memory."""
        from services.memory.service import MemoryService
        mem_service = MemoryService(self.db)
        user_id = kwargs.get("user_id", 0)
        results = mem_service.search_memories(
            query=inputs.get("query", ""),
            user_id=user_id,
        )
        return {"results": results}

    def _get_time_period(self, inputs: dict, **kwargs) -> dict:
        """Resolve time period to date boundaries."""
        from services.data_query.time_resolver import resolve_time_period
        period = inputs.get("period", "")
        result = resolve_time_period(period)
        return result

    def _create_chart_spec(self, inputs: dict, **kwargs) -> dict:
        """Create a chart specification."""
        return {
            "type": inputs.get("type", "bar"),
            "title": inputs.get("title", "Chart"),
            "x": inputs.get("x"),
            "y": inputs.get("y"),
            "data": inputs.get("data", []),
        }
