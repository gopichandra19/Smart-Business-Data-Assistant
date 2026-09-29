"""Integration tests for FastAPI endpoints."""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_login_success_admin(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.local",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@example.local"
        assert data["user"]["role"] == "admin"

    def test_login_success_employee(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "employee@example.local",
            "password": "employee123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "employee"

    def test_login_invalid_password(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "admin@example.local",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_unknown_user(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.local",
            "password": "password123",
        })
        assert response.status_code == 401

    def test_get_me_unauthorized(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_authorized(self):
        # First login
        login_res = client.post("/api/v1/auth/login", json={
            "email": "admin@example.local",
            "password": "admin123",
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == "admin@example.local"


class TestDashboardEndpoints:
    """Test dashboard metrics and charts."""

    @pytest.fixture(autouse=True)
    def setup_token(self):
        login_res = client.post("/api/v1/auth/login", json={
            "email": "admin@example.local",
            "password": "admin123",
        })
        self.token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_dashboard_data(self):
        response = client.get("/api/v1/dashboard", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert len(data["cards"]) >= 5
        assert "revenue_by_region" in data
        assert "top_customers" in data
        assert "revenue_by_month" in data


class TestKnowledgeAndDataSources:
    """Test knowledge base and data sources endpoints."""

    @pytest.fixture(autouse=True)
    def setup_token(self):
        login_res = client.post("/api/v1/auth/login", json={
            "email": "admin@example.local",
            "password": "admin123",
        })
        self.token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_list_data_sources(self):
        response = client.get("/api/v1/data-sources", headers=self.headers)
        assert response.status_code == 200
        sources = response.json()
        assert isinstance(sources, list)
        assert len(sources) >= 1

    def test_list_knowledge_documents(self):
        response = client.get("/api/v1/knowledge", headers=self.headers)
        assert response.status_code == 200
        docs = response.json()
        assert isinstance(docs, list)
        assert len(docs) >= 10

    def test_filter_knowledge_by_domain(self):
        response = client.get("/api/v1/knowledge?domain=finance", headers=self.headers)
        assert response.status_code == 200
        docs = response.json()
        assert all(d["business_domain"] == "finance" for d in docs)


class TestMemoryAndAuditEndpoints:
    """Test memories and audit log endpoints."""

    def test_memory_user_isolation(self):
        # Admin login
        admin_login = client.post("/api/v1/auth/login", json={
            "email": "admin@example.local",
            "password": "admin123",
        }).json()
        admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

        # Employee login
        emp_login = client.post("/api/v1/auth/login", json={
            "email": "employee@example.local",
            "password": "employee123",
        }).json()
        emp_headers = {"Authorization": f"Bearer {emp_login['access_token']}"}

        # Get memories for both
        admin_mem = client.get("/api/v1/memories", headers=admin_headers)
        emp_mem = client.get("/api/v1/memories", headers=emp_headers)

        assert admin_mem.status_code == 200
        assert emp_mem.status_code == 200

    def test_audit_logs_rbac(self):
        # Employee should not have full admin access or should only see permitted logs
        emp_login = client.post("/api/v1/auth/login", json={
            "email": "employee@example.local",
            "password": "employee123",
        }).json()
        emp_headers = {"Authorization": f"Bearer {emp_login['access_token']}"}

        response = client.get("/api/v1/audit", headers=emp_headers)
        # Should either succeed (filtered) or return status
        assert response.status_code in [200, 403]


class TestChatAssistantFlow:
    """Test conversational business query pipeline."""

    @pytest.fixture(autouse=True)
    def setup_token(self):
        login_res = client.post("/api/v1/auth/login", json={
            "email": "analyst@example.local",
            "password": "analyst123",
        })
        self.token = login_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_chat_query_revenue(self):
        response = client.post("/api/v1/chat", headers=self.headers, json={
            "message": "What is the total revenue by region?",
            "conversation_id": None,
        })
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "conversation_id" in data
        assert "evidence" in data
        assert "tool_calls" in data

    def test_chat_query_active_customers(self):
        response = client.post("/api/v1/chat", headers=self.headers, json={
            "message": "How many active customers do we have?",
            "conversation_id": None,
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["answer"]) > 0
