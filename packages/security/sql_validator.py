"""SQL safety validator - blocks dangerous operations, enforces read-only access."""

import re
from typing import Optional
from packages.observability.logging import get_logger

logger = get_logger("sql_safety")

# Blocked SQL keywords - case insensitive
BLOCKED_KEYWORDS = [
    r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
    r'\bALTER\b', r'\bTRUNCATE\b', r'\bCREATE\b', r'\bGRANT\b',
    r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b', r'\bMERGE\b',
    r'\bREPLACE\b', r'\bCALL\b', r'\bIMPORT\b', r'\bLOAD\b',
    r'\bATTACH\b', r'\bDETACH\b',
]

# Suspicious patterns
SUSPICIOUS_PATTERNS = [
    r';\s*\w',              # Multiple statements
    r'--\s',                # SQL comments that might hide injections
    r'/\*',                 # Block comments
    r'\bUNION\b.*\bSELECT\b',  # UNION injection
    r'\bINTO\s+OUTFILE\b',
    r'\bINTO\s+DUMPFILE\b',
    r'\bLOAD_FILE\b',
    r'\bBENCHMARK\b',
    r'\bSLEEP\b',
    r'\bWAITFOR\b',
    r'xp_cmdshell',
    r'information_schema',  # Schema probing
    r'pg_catalog',
    r'sqlite_master',
]

# Allowed tables for business queries
ALLOWED_TABLES = {
    "customers", "orders", "transactions", "products",
    "salespeople", "campaigns",
}

# Role-based table access
ROLE_TABLE_ACCESS = {
    "employee": {"customers", "products", "orders", "campaigns"},
    "manager": {"customers", "products", "orders", "transactions", "salespeople", "campaigns"},
    "analyst": {"customers", "products", "orders", "transactions", "salespeople", "campaigns"},
    "admin": {"customers", "products", "orders", "transactions", "salespeople", "campaigns"},
}

# Restricted columns per role
RESTRICTED_COLUMNS = {
    "employee": {"email", "phone", "salary", "password_hash", "connection_config", "cost", "profit"},
    "manager": {"salary", "password_hash", "connection_config"},
    "analyst": {"password_hash", "connection_config"},
    "admin": {"password_hash"},
}


class SQLValidationResult:
    """Result of SQL validation."""

    def __init__(self, is_valid: bool, sql: str, errors: list[str] = None):
        self.is_valid = is_valid
        self.sql = sql
        self.errors = errors or []


def validate_sql(
    sql: str,
    user_role: str = "analyst",
    allowed_tables: set[str] | None = None,
    max_rows: int = 1000,
) -> SQLValidationResult:
    """
    Validate SQL for safety. Returns validation result.

    Rules:
    1. Only SELECT statements allowed
    2. No blocked keywords
    3. No suspicious patterns
    4. Only allowed tables
    5. No restricted columns for user's role
    6. Row limit enforced
    """
    errors = []
    cleaned = sql.strip()

    if not cleaned:
        return SQLValidationResult(False, sql, ["Empty SQL query"])

    # 1. Must start with SELECT (or WITH for CTEs)
    upper_sql = cleaned.upper().lstrip()
    if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
        errors.append("Only SELECT queries are permitted. Query must start with SELECT or WITH.")
        return SQLValidationResult(False, sql, errors)

    # 2. Check blocked keywords
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            keyword = re.search(pattern, cleaned, re.IGNORECASE).group()
            errors.append(f"Blocked SQL keyword detected: {keyword}")
            logger.warning("sql_blocked_keyword", keyword=keyword, sql=sql[:200])

    # 3. Check suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            errors.append(f"Suspicious SQL pattern detected")
            logger.warning("sql_suspicious_pattern", pattern=pattern[:50], sql=sql[:200])

    # 4. Check allowed tables
    role_tables = ROLE_TABLE_ACCESS.get(user_role, ALLOWED_TABLES)
    tables = allowed_tables or role_tables
    # Extract table references (simplified parser)
    table_pattern = r'\b(?:FROM|JOIN)\s+(\w+)'
    referenced_tables = set(
        match.lower() for match in re.findall(table_pattern, cleaned, re.IGNORECASE)
    )
    disallowed = referenced_tables - tables
    if disallowed:
        errors.append(f"Access denied to tables: {', '.join(disallowed)}")

    # 5. Check restricted columns
    restricted = RESTRICTED_COLUMNS.get(user_role, set())
    if restricted:
        for col in restricted:
            col_pattern = rf'\b{re.escape(col)}\b'
            if re.search(col_pattern, cleaned, re.IGNORECASE):
                errors.append(f"Access denied to restricted column: {col}")

    # 6. Enforce LIMIT
    if not re.search(r'\bLIMIT\b', cleaned, re.IGNORECASE):
        cleaned = cleaned.rstrip(';') + f" LIMIT {max_rows}"

    if errors:
        return SQLValidationResult(False, sql, errors)

    return SQLValidationResult(True, cleaned, [])


def sanitize_for_prompt(text: str) -> str:
    """
    Sanitize text that will be included in LLM prompts.
    Treats all external data as untrusted.
    """
    if not text:
        return ""
    # Remove potential prompt injection markers
    injection_patterns = [
        r'ignore\s+(all\s+)?(previous\s+)?instructions',
        r'forget\s+(all\s+)?previous',
        r'you\s+are\s+now',
        r'new\s+instructions?\s*:',
        r'system\s*:\s*',
        r'<\s*system\s*>',
        r'</?\s*prompt\s*>',
        r'ADMIN\s+OVERRIDE',
    ]
    cleaned = text
    for pattern in injection_patterns:
        cleaned = re.sub(pattern, '[FILTERED]', cleaned, flags=re.IGNORECASE)
    return cleaned
