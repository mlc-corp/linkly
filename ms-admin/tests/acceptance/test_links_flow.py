import pytest
import time
import sys
import os
import requests
import logging # Usar logging
from fastapi.testclient import TestClient

# --- CAMBIO EN IMPORTACIÓN ---
# Ya no importamos 'table' directamente
# from app.db.dynamo import table 
from app.db.dynamo import get_table # Importamos la función
# -----------------------------

from app.main import app # Importa tu app FastAPI

# Configuración de logging para pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Base URL configurable (esto está bien) ---
BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8080") # Usa 8080 si es el puerto de FastAPI/uvicorn
# Nota: TestClient no necesita base_url si las rutas son relativas (ej: "/links")
client = TestClient(app) 


@pytest.fixture
def link_payload():
    """Payload de ejemplo para crear un link."""
    # Añade un slug único para cada ejecución de prueba para evitar colisiones
    timestamp = int(time.time() * 1000)
    return {
        "title": f"E2E Acceptance Link {timestamp}",
        "slug": f"e2e-test-{timestamp}", # Slug único
        "destinationUrl": "http://example.com/e2e",
        "variants": ["default", "variant1"],
    }


def wait_for_table_ready(timeout: int = 15):
    """
    Espera a que DynamoDB (Local o AWS) esté lista y accesible.
    """
    logger.info("Esperando a que DynamoDB esté lista...")
    # --- Obtiene la tabla (y por ende, la conexión) ---
    try:
        table = get_table() 
        endpoint_url = table.meta.client.meta.endpoint_url
        logger.info(f"Intentando conectar a DynamoDB en: {endpoint_url}")
    except Exception as e:
         pytest.fail(f"Fallo al inicializar la conexión a DynamoDB ({e})")

    # --- Esperar a que la tabla responda a una operación básica ---
    start_time = time.time()
    last_error = None
    while time.time() - start_time < timeout:
        try:
            # Intenta una operación simple como describe_table
            table.meta.client.describe_table(TableName=table.name)
            logger.info(f"✅ DynamoDB lista y tabla '{table.name}' accesible.")
            return # Éxito, la tabla está lista
        except requests.exceptions.ConnectionError as ce:
            logger.warning(f"Esperando conexión a {endpoint_url}...")
            last_error = ce
            time.sleep(1)
        except table.meta.client.exceptions.ResourceNotFoundException:
             pytest.fail(f"La tabla '{table.name}' no existe en {endpoint_url}.")
        except Exception as e:
            # Captura otros errores (ej: credenciales, throttling)
            logger.warning(f"Esperando a DynamoDB... (Error: {e})")
            last_error = e
            time.sleep(1)
            
    # Si sale del bucle, falló
    pytest.fail(f"DynamoDB no estuvo lista en {timeout}s. Último error: {last_error}")


# --- Test E2E principal ---
def test_links_endpoints_e2e(link_payload):
    """Prueba completa del flujo CRUD de links."""
    
    # Espera a que la base de datos esté lista ANTES de empezar
    wait_for_table_ready()
    
    # Obtiene la referencia a la tabla UNA VEZ al inicio del test
    table = get_table() 
    
    logger.info(f"Ejecutando prueba E2E con payload: {link_payload}")

    # --- Crear link ---
    logger.info("Probando POST /links...")
    # Usa rutas relativas con TestClient
    response = client.post("/links", json=link_payload) 
    assert response.status_code == 201, f"Falló POST /links. Response: {response.text}"
    created = response.json()
    link_id = created.get("linkId")
    assert link_id, "La respuesta de POST /links no incluyó linkId"
    
    # Usa el slug del payload, ya que ahora es único y requerido (o el generado si es None)
    expected_slug = link_payload["slug"] 
    assert created.get("slug") == expected_slug, "El slug devuelto no coincide"
    logger.info(f"Link creado: {link_id}, Slug: {expected_slug}")

    # --- Verificar en Dynamo ---
    logger.info(f"Verificando creación en DynamoDB para linkId: {link_id}...")
    # Define las claves correctas según tu esquema
    key_meta = {"PK": f"LINK#{link_id}", "SK": "META"}
    key_alias = {"PK": f"LINK#{expected_slug}", "SK": "ALIAS"} 
    
    try:
        result_meta = table.get_item(Key=key_meta)
        item_meta = result_meta.get("Item")
        assert item_meta, f"No se encontró el item maestro {key_meta} en DynamoDB"
        assert item_meta.get("title") == link_payload["title"], "El título en DB no coincide"
        logger.info("Item maestro verificado en DB.")

        result_alias = table.get_item(Key=key_alias)
        item_alias = result_alias.get("Item")
        assert item_alias, f"No se encontró el item alias {key_alias} en DynamoDB"
        assert item_alias.get("linkId") == link_id, "El linkId en el alias no coincide"
        logger.info("Item alias verificado en DB.")

    except Exception as e:
        pytest.fail(f"Error al verificar en DynamoDB: {e}")


    # --- Listar links ---
    logger.info("Probando GET /links...")
    response = client.get("/links")
    assert response.status_code == 200, f"Falló GET /links. Response: {response.text}"
    items = response.json().get("items", [])
    assert isinstance(items, list), "La respuesta de GET /links no contiene una lista 'items'"
    # Busca el link creado en la lista
    found = any(i.get("linkId") == link_id for i in items)
    assert found, f"El link {link_id} no se encontró en la lista de GET /links"
    logger.info("Listar links verificado.")

    # --- Obtener link ---
    logger.info(f"Probando GET /links/{link_id}...")
    response = client.get(f"/links/{link_id}")
    assert response.status_code == 200, f"Falló GET /links/{link_id}. Response: {response.text}"
    item = response.json()
    assert item.get("linkId") == link_id, "El linkId devuelto por GET /links/{id} no coincide"
    logger.info("Obtener link verificado.")

    # --- Obtener métricas ---
    logger.info(f"Probando GET /links/{link_id}/metrics...")
    response = client.get(f"/links/{link_id}/metrics")
    assert response.status_code == 200, f"Falló GET /links/{link_id}/metrics. Response: {response.text}"
    metrics = response.json()
    assert metrics.get("slug") == expected_slug, "El slug en las métricas no coincide"
    # Puedes añadir más aserciones sobre la estructura de las métricas si quieres
    assert "totals" in metrics, "La respuesta de métricas no incluye 'totals'"
    logger.info("Obtener métricas verificado.")

    # --- Borrar link ---
    logger.info(f"Probando DELETE /links/{link_id}...")
    response = client.delete(f"/links/{link_id}")
    # Espera 204 No Content para DELETE exitoso
    assert response.status_code == 204, f"Falló DELETE /links/{link_id}. Response: {response.text}" 
    logger.info("Borrar link verificado.")

    # --- Confirmar que se eliminó ---
    logger.info(f"Confirmando eliminación con GET /links/{link_id}...")
    response = client.get(f"/links/{link_id}")
    # Espera 404 Not Found después de borrar
    assert response.status_code == 404, f"GET /links/{link_id} debería dar 404 después de borrar, pero dio {response.status_code}"
    logger.info("Eliminación confirmada.")
    
    # --- Confirmar que alias también se eliminó (Opcional pero bueno) ---
    logger.info(f"Confirmando eliminación de alias en DB para slug: {expected_slug}...")
    try:
        result_alias_after_delete = table.get_item(Key=key_alias)
        item_alias_after_delete = result_alias_after_delete.get("Item")
        assert item_alias_after_delete is None, f"El item alias {key_alias} todavía existe en DynamoDB después de borrar"
        logger.info("Eliminación de alias confirmada en DB.")
    except Exception as e:
         pytest.fail(f"Error al verificar eliminación de alias en DynamoDB: {e}")

    logger.info("✅ Prueba E2E completada exitosamente.")
