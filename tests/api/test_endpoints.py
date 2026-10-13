"""
API endpoint tests for the test_endpoints.py file.
Covers chat endpoint validation and header requirements.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_chat_validation_no_body(client: TestClient) -> None:
    """POST /chat with no body should fail with 422."""
    response = client.post("/chat")
    assert response.status_code == 422


def test_chat_validation_empty_body(client: TestClient) -> None:
    """POST /chat with empty JSON should fail with 422."""
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_validation_missing_thread_id(client: TestClient) -> None:
    """thread_id is optional (has default_factory=uuid4)   omitting it is valid.
    The request will reach the graph (which may 500 without live DB) but never 422.
    """
    response = client.post("/chat", json={"message": "Hello"})
    # Not a 422 (schema error) since thread_id has a default
    assert response.status_code in (200, 500)  # 500 ok   no live DB in CI


def test_chat_validation_missing_message(client: TestClient) -> None:
    response = client.post("/chat", json={"thread_id": str(uuid4())})
    assert response.status_code == 422


def test_chat_validation_bad_uuid(client: TestClient) -> None:
    response = client.post("/chat", json={"thread_id": "bad-uuid", "message": "Hi"})
    assert response.status_code == 422


def test_health_endpoint_is_accessible(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "healthy"
