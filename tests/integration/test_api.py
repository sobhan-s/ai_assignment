"""
Integration tests for the FastAPI HTTP layer.
Tests run against the real FastAPI app using TestClient (no real DB or LLM).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_health_check_returns_200(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_structure(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()
    assert "status" in body
    assert body["status"] == "healthy"


def test_health_check_includes_provider_info(client: TestClient) -> None:
    response = client.get("/health")
    body = response.json()
    assert "llm_provider" in body
    assert "llm_model" in body
    assert "embedding_provider" in body
    assert "embedding_model" in body


# /chat endpoint   validation


def test_chat_endpoint_missing_body_returns_422(client: TestClient) -> None:
    response = client.post("/chat")
    assert response.status_code == 422


def test_chat_endpoint_empty_json_returns_422(client: TestClient) -> None:
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_endpoint_missing_message_returns_422(client: TestClient) -> None:
    response = client.post("/chat", json={"thread_id": str(uuid4())})
    assert response.status_code == 422


def test_chat_endpoint_missing_thread_id_uses_default(client: TestClient) -> None:
    """thread_id has default_factory=uuid4, so omitting it is valid at the schema level.
    When thread_id is missing, the schema auto-generates one and proceeds to the graph.
    The graph may fail with 500 due to missing DB, but it must NOT be a schema error (422).
    """
    response = client.post("/chat", json={"message": "Hello"})
    # Should not be a 422 (schema validation error)   thread_id is optional
    assert response.status_code in (200, 500)  # 500 acceptable   no live DB in test env


def test_chat_endpoint_invalid_thread_id_returns_422(client: TestClient) -> None:
    response = client.post(
        "/chat", json={"thread_id": "not-a-uuid", "message": "Hello"}
    )
    assert response.status_code == 422


# /documents endpoint   validation


def test_documents_ingest_no_file_returns_422(client: TestClient) -> None:
    response = client.post("/documents/ingest")
    assert response.status_code == 422


# Content-type headers


def test_health_returns_json_content_type(client: TestClient) -> None:
    response = client.get("/health")
    assert "application/json" in response.headers.get("content-type", "")
