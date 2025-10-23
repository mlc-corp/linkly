import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch
import uuid
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def link_payload():
    return {
        "title": "Acceptance Test Link",
        "destinationUrl": "http://example.com",
        "variants": ["default", "variant1"]
    }

@pytest.fixture(autouse=True)
def mock_dynamodb_tables():
    db = {}  # almacen simulado

    with patch("app.services.link_service.table") as link_table_mock, \
         patch("app.services.metrics_service.table") as metrics_table_mock:

        # función genérica para mocks
        def create_side_effect(table_mock):
            def put_item(Item, **kwargs):
                pk = Item.get("PK") or f"LINK#{Item.get('linkId', str(uuid.uuid4()))}"
                sk = Item.get("SK") or "META"
                db[(pk, sk)] = Item
                return {"ResponseMetadata": {"HTTPStatusCode": 200}}

            def get_item(Key, **kwargs):
                pk = Key.get("PK")
                sk = Key.get("SK")
                item = db.get((pk, sk))
                return {"Item": item} if item else {}

            def scan(**kwargs):
                return {"Items": list(db.values())}

            def delete_item(Key, **kwargs):
                pk = Key.get("PK")
                sk = Key.get("SK")
                db.pop((pk, sk), None)
                return {"ResponseMetadata": {"HTTPStatusCode": 200}}

            table_mock.put_item.side_effect = put_item
            table_mock.get_item.side_effect = get_item
            table_mock.scan.side_effect = scan
            table_mock.delete_item.side_effect = delete_item

        # aplicamos a ambos mocks
        create_side_effect(link_table_mock)
        create_side_effect(metrics_table_mock)

        yield

def test_links_endpoints_flow(link_payload):
    # --- Crear link ---
    response = client.post("/links", json=link_payload)
    assert response.status_code == 201
    created_link = response.json()
    link_id = created_link["linkId"]

    expected_slug = link_payload["title"].lower().replace(" ", "-")
    assert created_link["slug"] == expected_slug
    assert created_link["title"] == link_payload["title"]
    assert set(created_link["variants"]) == set(link_payload["variants"])
    assert "createdAt" in created_link

    # --- Listar links ---
    response = client.get("/links")
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(item["linkId"] == link_id for item in items)

    # --- Obtener link por ID ---
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 200
    item = response.json()
    assert item["linkId"] == link_id
    assert item["slug"] == expected_slug

    # --- Obtener link que no existe ---
    response = client.get("/links/nonexistent-id")
    assert response.status_code == 404

    # --- Obtener métricas ---
    response = client.get(f"/links/{link_id}/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["slug"] == expected_slug

    # --- Borrar link ---
    response = client.delete(f"/links/{link_id}")
    assert response.status_code == 204

    # --- Verificar que ya no existe ---
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 404
