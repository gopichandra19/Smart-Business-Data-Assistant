"""Unit tests for time period resolver."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import date
from services.data_query.time_resolver import resolve_time_period


class TestTimePeriodResolver:
    """Test deterministic time period resolution."""

    REF = date(2026, 9, 15)  # Reference: September 15, 2026

    def test_today(self):
        result = resolve_time_period("today", self.REF)
        assert result["start_date"] == "2026-09-15"
        assert result["end_date"] == "2026-09-15"

    def test_yesterday(self):
        result = resolve_time_period("yesterday", self.REF)
        assert result["start_date"] == "2026-09-14"

    def test_this_month(self):
        result = resolve_time_period("this month", self.REF)
        assert result["start_date"] == "2026-09-01"
        assert result["end_date"] == "2026-09-15"

    def test_last_month(self):
        result = resolve_time_period("last month", self.REF)
        assert result["start_date"] == "2026-08-01"
        assert result["end_date"] == "2026-08-31"

    def test_this_quarter(self):
        result = resolve_time_period("this quarter", self.REF)
        assert result["start_date"] == "2026-07-01"

    def test_last_quarter(self):
        result = resolve_time_period("last quarter", self.REF)
        assert result["start_date"] == "2026-04-01"
        assert result["end_date"] == "2026-06-30"
        assert "Q2" in result["label"]

    def test_specific_quarter(self):
        result = resolve_time_period("Q3 2025", self.REF)
        assert result["start_date"] == "2025-07-01"
        assert result["end_date"] == "2025-09-30"

    def test_this_year(self):
        result = resolve_time_period("this year", self.REF)
        assert result["start_date"] == "2026-01-01"

    def test_last_year(self):
        result = resolve_time_period("last year", self.REF)
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-12-31"

    def test_last_n_months(self):
        result = resolve_time_period("last 6 months", self.REF)
        assert result["start_date"] == "2026-03-15"

    def test_last_n_days(self):
        result = resolve_time_period("last 30 days", self.REF)
        assert result["start_date"] == "2026-08-16"

    def test_specific_year(self):
        result = resolve_time_period("2024", self.REF)
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"

    def test_specific_month(self):
        result = resolve_time_period("2025-06", self.REF)
        assert result["start_date"] == "2025-06-01"
        assert result["end_date"] == "2025-06-30"

    def test_unknown_period_defaults(self):
        result = resolve_time_period("when the moon is blue", self.REF)
        assert result["start_date"]  # Should default to last 90 days
        assert result["end_date"]


class TestAuthorizationService:
    """Test RBAC permissions."""

    def test_setup(self):
        from services.authorization.service import AuthorizationService
        self.auth = AuthorizationService()

    def test_employee_permissions(self):
        from services.authorization.service import AuthorizationService
        auth = AuthorizationService()
        assert auth.check_permission("employee", "chat")
        assert auth.check_permission("employee", "view_dashboard")
        assert not auth.check_permission("employee", "manage_data_sources")
        assert not auth.check_permission("employee", "view_audit")

    def test_admin_permissions(self):
        from services.authorization.service import AuthorizationService
        auth = AuthorizationService()
        assert auth.check_permission("admin", "chat")
        assert auth.check_permission("admin", "manage_data_sources")
        assert auth.check_permission("admin", "view_audit")
        assert auth.check_permission("admin", "manage_users")

    def test_table_access_employee(self):
        from services.authorization.service import AuthorizationService
        auth = AuthorizationService()
        assert auth.check_table_access("employee", "customers")
        assert not auth.check_table_access("employee", "transactions")
        assert not auth.check_table_access("employee", "salespeople")

    def test_table_access_analyst(self):
        from services.authorization.service import AuthorizationService
        auth = AuthorizationService()
        assert auth.check_table_access("analyst", "transactions")
        assert auth.check_table_access("analyst", "salespeople")

    def test_column_restrictions(self):
        from services.authorization.service import AuthorizationService
        auth = AuthorizationService()
        assert not auth.check_column_access("employee", "email")
        assert not auth.check_column_access("employee", "salary")
        assert auth.check_column_access("admin", "email")
        assert not auth.check_column_access("admin", "password_hash")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
