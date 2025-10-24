import pytest
import time
import sys
import os
import requests

from fastapi.testclient import TestClient
from app.main import app
from app.db.dynamo import table

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

client = TestClient(app)


@pytest.fixture
def link_payload():
    return {
        "title": "E2E Acceptance Link",
        "destinationUrl": "http://example.com",
        "variants": ["default", "variant1"],
    }


def wait_for_table_ready(timeout: int = 10):
    """
    Espera a que DynamoDB Local esté lista antes de correr las pruebas.
    Falla explícitamente si no se puede conectar al endpoint o la tabla no responde.
    """
    endpoint_url = table.meta.client.meta.endpoint_url
    print(f"Verificando conexión a DynamoDB: {endpoint_url}")

    # --- Verificar que el endpoint responda ---
    try:
        resp = requests.get(endpoint_url, timeout=2)
        print(f"DynamoDB endpoint activo: {endpoint_url} (status {resp.status_code})")
    except Exception as e:
        pytest.fail(f"❌ No se pudo conectar al endpoint {endpoint_url}: {e}")

    # --- Esperar a que la tabla esté lista ---
    for _ in range(timeout):
        try:
            _ = table.table_status
            return
        except Exception:
            time.sleep(1)
    pytest.fail(f"DynamoDB Local no está lista después de {timeout}s")


def test_links_endpoints_e2e(link_payload):
    wait_for_table_ready()

    # --- Crear link ---
    response = client.post("/links", json=link_payload)
    assert response.status_code == 201, response.text
    created = response.json()
    link_id = created["linkId"]

    expected_slug = link_payload["title"].lower().replace(" ", "-")
    assert created["slug"] == expected_slug

    # --- Verificar en Dynamo ---
    key = {"PK": f"LINK#{link_id}", "SK": "META"}
    result = table.get_item(Key=key)
    item = result.get("Item")
    assert item, f"No se encontró el item {key} en DynamoDB"
    assert item["title"] == link_payload["title"]

    # --- Listar links ---
    response = client.get("/links")
    assert response.status_code == 200
    items = response.json()["items"]
    assert any(i["linkId"] == link_id for i in items)

    # --- Obtener link ---
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 200
    item = response.json()
    assert item["linkId"] == link_id

    # --- Obtener métricas ---
    response = client.get(f"/links/{link_id}/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["slug"] == expected_slug

    # --- Borrar link ---
    response = client.delete(f"/links/{link_id}")
    assert response.status_code == 204

    # --- Confirmar que se eliminó ---
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 404
