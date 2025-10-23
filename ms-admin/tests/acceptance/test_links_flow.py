import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def link_payload():
    return {
        "title": "Acceptance Test Link",
        "slug": "acceptance-test-link",
        "destinationUrl": "http://example.com",
        "variants": ["default", "variant1"]
    }

def test_links_endpoints_flow(link_payload):
    # --- Crear link ---
    response = client.post("/links", json=link_payload)
    assert response.status_code == 201
    created_link = response.json()
    link_id = created_link["linkId"]

    assert created_link["slug"] == link_payload["slug"]
    assert created_link["title"] == link_payload["title"]
    assert created_link["destinationUrl"].rstrip("/") == link_payload["destinationUrl"].rstrip("/")
    assert set(created_link["variants"]) == set(link_payload["variants"])
    assert "createdAt" in created_link

    # --- Listar links ---
    response = client.get("/links")
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(l["linkId"] == link_id for l in items)

    # --- Obtener link por ID ---
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 200
    item = response.json()
    assert item["linkId"] == link_id
    assert item["slug"] == link_payload["slug"]

    # --- Obtener link que no existe ---
    response = client.get("/links/nonexistent-id")
    assert response.status_code == 404

    # --- Obtener métricas ---
    response = client.get(f"/links/{link_id}/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["slug"] == link_payload["slug"]
    assert "totals" in metrics
    assert "clicks" in metrics["totals"]
    assert "byVariant" in metrics["totals"]
    assert "byDevice" in metrics["totals"]
    assert "byCountry" in metrics["totals"]

    # --- Borrar link ---
    response = client.delete(f"/links/{link_id}")
    assert response.status_code == 204

    # --- Verificar que ya no existe ---
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 404
