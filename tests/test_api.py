from fastapi.testclient import TestClient

from conftest import demo_service
from morocco_legal_rag.api import create_app


def test_health_and_grounded_answer() -> None:
    client = TestClient(create_app(demo_service()))
    homepage = client.get("/")
    assert homepage.status_code == 200
    assert "MOROCCO" in homepage.text
    assert "LEGAL RAG" in homepage.text
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["indexed_chunks"] == 3

    response = client.post(
        "/ask",
        json={"question": "Quel est le délai de traitement ?", "language": "fr", "top_k": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answerable"] is True
    assert payload["citations"][0]["source_id"] == "A"
    assert "avis juridique" in payload["warning"]


def test_api_abstains_outside_corpus() -> None:
    client = TestClient(create_app(demo_service()))
    response = client.post(
        "/ask",
        json={"question": "Quelle météo demain à Casablanca ?", "language": "fr", "top_k": 3},
    )
    payload = response.json()
    assert payload["answerable"] is False
    assert payload["citations"] == []
