"""Authorization service - RBAC, field-level access, and approval framework."""

from typing import Optional
from packages.database.models import UserRole
from packages.observability.logging import get_logger

logger = get_logger("authorization")


# Permission matrix: role → set of allowed capabilities
ROLE_PERMISSIONS = {
    "employee": {
        "chat", "view_dashboard", "view_own_conversations",
        "view_own_memories", "delete_own_memories",
        "basic_analytics", "view_knowledge",
    },
    "manager": {
        "chat", "view_dashboard", "view_own_conversations",
        "view_own_memories", "delete_own_memories",
        "basic_analytics", "view_knowledge",
        "department_reports", "aggregations", "saved_analyses",
        "view_team_analytics",
    },
    "analyst": {
        "chat", "view_dashboard", "view_own_conversations",
        "view_own_memories", "delete_own_memories",
        "basic_analytics", "view_knowledge",
        "advanced_analytics", "query_inspection", "schema_inspection",
        "department_reports", "aggregations", "saved_analyses",
        "export_data",
    },
    "admin": {
        "chat", "view_dashboard", "view_own_conversations",
        "view_own_memories", "delete_own_memories",
        "basic_analytics", "view_knowledge",
        "advanced_analytics", "query_inspection", "schema_inspection",
        "department_reports", "aggregations", "saved_analyses",
        "export_data",
        "manage_data_sources", "manage_knowledge", "manage_users",
        "view_audit", "manage_settings", "view_all_memories",
    },
}

# Tables accessible by role
TABLE_ACCESS = {
    "employee": {"customers", "products", "orders", "campaigns"},
    "manager": {"customers", "products", "orders", "transactions", "campaigns"},
    "analyst": {"customers", "products", "orders", "transactions", "salespeople", "campaigns"},
    "admin": {"customers", "products", "orders", "transactions", "salespeople", "campaigns"},
}

# Columns restricted per role
RESTRICTED_COLUMNS = {
    "employee": {"email", "phone", "salary", "password_hash", "connection_config", "cost", "profit"},
    "manager": {"salary", "password_hash", "connection_config"},
    "analyst": {"password_hash", "connection_config"},
    "admin": {"password_hash"},
}


class AuthorizationService:
    """Role-based access control and field-level authorization."""

    @staticmethod
    def check_permission(user_role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        perms = ROLE_PERMISSIONS.get(user_role, set())
        allowed = permission in perms
        if not allowed:
            logger.warning("permission_denied", role=user_role, permission=permission)
        return allowed

    @staticmethod
    def get_accessible_tables(user_role: str) -> set[str]:
        """Get tables accessible to a role."""
        return TABLE_ACCESS.get(user_role, set())

    @staticmethod
    def get_restricted_columns(user_role: str) -> set[str]:
        """Get columns restricted for a role."""
        return RESTRICTED_COLUMNS.get(user_role, set())

    @staticmethod
    def check_table_access(user_role: str, table_name: str) -> bool:
        """Check if user can access a specific table."""
        return table_name in TABLE_ACCESS.get(user_role, set())

    @staticmethod
    def check_column_access(user_role: str, column_name: str) -> bool:
        """Check if user can access a specific column."""
        restricted = RESTRICTED_COLUMNS.get(user_role, set())
        return column_name.lower() not in restricted

    @staticmethod
    def filter_query_tables(user_role: str, requested_tables: set[str]) -> tuple[set[str], set[str]]:
        """
        Filter requested tables against role permissions.
        Returns (allowed, denied) sets.
        """
        allowed = TABLE_ACCESS.get(user_role, set())
        permitted = requested_tables & allowed
        denied = requested_tables - allowed
        return permitted, denied

    @staticmethod
    def requires_approval(action: str, user_role: str) -> bool:
        """Check if an action requires human approval."""
        approval_required = {
            "delete_data_source": {"employee", "manager", "analyst"},
            "bulk_export": {"employee"},
            "modify_knowledge": {"employee", "manager"},
            "modify_user": {"employee", "manager", "analyst"},
        }
        return user_role in approval_required.get(action, set())
