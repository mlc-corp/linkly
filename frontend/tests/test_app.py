# tests/test_app.py
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app  # ahora sí funcionará


@pytest.fixture
def client():
    """Crea un cliente de prueba de Flask usando la factory."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_root_redirects_to_app(client):
    """Verifica que la raíz redirige a /app."""
    response = client.get('/')
    assert response.status_code in (301, 302)
    assert '/app' in response.headers['Location']


def test_app_home_returns_html(client):
    """Verifica que /app devuelve el HTML principal."""
    response = client.get('/app')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'Linkly' in response.data
    assert b'Crear Nuevo Link' in response.data


def test_link_detail_returns_html(client):
    """Verifica que /app/links/<id> renderiza la plantilla detalle."""
    response = client.get('/app/links/lk_test123')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'Detalle del Link' in response.data
    assert b'linkIdData' in response.data


def test_health_endpoint_ok(client):
    """Verifica que /health devuelve un JSON correcto."""
    response = client.get('/health')
    data = response.get_json()
    assert response.status_code == 200
    assert data['ok'] is True


def test_api_links_get(client):
    """Verifica que /api/links devuelve un JSON válido (aunque esté vacío)."""
    response = client.get('/api/links')
    assert response.status_code in (200, 503, 500)
    assert b'{' in response.data


def test_api_link_detail_not_found(client):
    """Verifica que /api/links/<id> responde correctamente si no existe."""
    response = client.get('/api/links/lk_inexistente')
    assert response.status_code in (404, 503, 500)
    assert b'error' in response.data or b'No se pudo conectar' in response.data


def test_api_create_link_without_body(client):
    """Verifica que /api/links devuelve error 400 si no se envían datos."""
    response = client.post('/api/links', json=None)
    data = response.get_json()
    assert response.status_code == 400
    assert 'error' in data
    assert 'No se enviaron datos' in data['error']


def test_api_health_check(client):
    """Verifica que /api/health responde con estructura esperada."""
    response = client.get('/api/health')
    data = response.get_json()
    assert response.status_code in (200, 503)
    assert 'frontend' in data
    assert 'msAdmin' in data