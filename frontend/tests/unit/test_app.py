# tests/test_app.py
import os
import sys
import pytest
from unittest.mock import patch, Mock
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


@pytest.fixture
def client():
    """Crea un cliente de prueba de Flask usando la factory."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_link_service():
    """Mock del servicio de links."""
    with patch('routes.api_routes.link_service') as mock:
        yield mock


# ============================================================================
# TESTS DE WEB ROUTES
# ============================================================================

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


# ============================================================================
# TESTS DE API ROUTES - GET /api/links
# ============================================================================

def test_api_links_get_success(client, mock_link_service):
    """Verifica obtención exitosa de links."""
    mock_link_service.get_all_links.return_value = [
        {'linkId': 'lk_1', 'slug': 'test1'},
        {'linkId': 'lk_2', 'slug': 'test2'}
    ]
    
    response = client.get('/api/links')
    data = response.get_json()
    
    assert response.status_code == 200
    assert len(data['items']) == 2


def test_api_links_get_connection_error(client, mock_link_service):
    """Verifica manejo de errores de conexión en GET /api/links."""
    mock_link_service.get_all_links.side_effect = requests.RequestException()
    
    response = client.get('/api/links')
    assert response.status_code == 503


def test_api_links_get_unexpected_error(client, mock_link_service):
    """Verifica manejo de errores inesperados en GET /api/links."""
    mock_link_service.get_all_links.side_effect = Exception("Error inesperado")
    
    response = client.get('/api/links')
    assert response.status_code == 500


# ============================================================================
# TESTS DE API ROUTES - POST /api/links
# ============================================================================

def test_api_create_link_without_body(client):
    """Verifica que /api/links devuelve error 400 si no se envían datos."""
    response = client.post('/api/links', json=None)
    data = response.get_json()
    assert response.status_code == 400
    assert 'error' in data
    assert 'No se enviaron datos' in data['error']


def test_api_create_link_success(client, mock_link_service):
    """Verifica creación exitosa de un link."""
    mock_link_service.create_link.return_value = {
        'linkId': 'lk_new',
        'slug': 'test-slug',
        'title': 'Test'
    }
    
    response = client.post('/api/links', json={
        'title': 'Test',
        'slug': 'test-slug',
        'destinationUrl': 'https://example.com',
        'variants': ['ig', 'fb']
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['slug'] == 'test-slug'


def test_api_create_link_validation_error(client, mock_link_service):
    """Verifica manejo de errores de validación."""
    mock_link_service.create_link.side_effect = ValueError('El título es requerido')
    
    response = client.post('/api/links', json={
        'title': '',
        'slug': 'test',
        'destinationUrl': 'https://example.com'
    })
    
    assert response.status_code == 400


def test_api_create_link_connection_error(client, mock_link_service):
    """Verifica manejo de errores de conexión en POST /api/links."""
    mock_link_service.create_link.side_effect = requests.RequestException()
    
    response = client.post('/api/links', json={
        'title': 'Test',
        'slug': 'test',
        'destinationUrl': 'https://example.com'
    })
    
    assert response.status_code == 503


def test_api_create_link_unexpected_error(client, mock_link_service):
    """Verifica manejo de errores inesperados en POST /api/links."""
    mock_link_service.create_link.side_effect = Exception("Error inesperado")
    
    response = client.post('/api/links', json={
        'title': 'Test',
        'slug': 'test',
        'destinationUrl': 'https://example.com'
    })
    
    assert response.status_code == 500


# ============================================================================
# TESTS DE API ROUTES - GET /api/links/<link_id>
# ============================================================================

def test_api_link_detail_success(client, mock_link_service):
    """Verifica obtención exitosa de un link."""
    mock_link_service.get_link_by_id.return_value = {
        'linkId': 'lk_1',
        'slug': 'test',
        'title': 'Test Link'
    }
    
    response = client.get('/api/links/lk_1')
    data = response.get_json()
    
    assert response.status_code == 200
    assert data['slug'] == 'test'


def test_api_link_detail_not_found(client, mock_link_service):
    """Verifica que /api/links/<id> responde correctamente si no existe."""
    mock_link_service.get_link_by_id.return_value = None
    
    response = client.get('/api/links/lk_inexistente')
    assert response.status_code == 404


def test_api_link_detail_connection_error(client, mock_link_service):
    """Verifica manejo de errores de conexión en GET /api/links/<id>."""
    mock_link_service.get_link_by_id.side_effect = requests.RequestException()
    
    response = client.get('/api/links/lk_1')
    assert response.status_code == 503


def test_api_link_detail_unexpected_error(client, mock_link_service):
    """Verifica manejo de errores inesperados en GET /api/links/<id>."""
    mock_link_service.get_link_by_id.side_effect = Exception("Error inesperado")
    
    response = client.get('/api/links/lk_1')
    assert response.status_code == 500


# ============================================================================
# TESTS DE API ROUTES - DELETE /api/links/<link_id>
# ============================================================================

def test_api_delete_link_success(client, mock_link_service):
    """Verifica eliminación exitosa de un link."""
    mock_link_service.delete_link.return_value = True
    
    response = client.delete('/api/links/lk_1')
    assert response.status_code == 204


def test_api_delete_link_not_found(client, mock_link_service):
    """Verifica respuesta cuando el link a eliminar no existe."""
    mock_link_service.delete_link.return_value = False
    
    response = client.delete('/api/links/lk_inexistente')
    assert response.status_code == 404


def test_api_delete_link_connection_error(client, mock_link_service):
    """Verifica manejo de errores de conexión en DELETE /api/links/<id>."""
    mock_link_service.delete_link.side_effect = requests.RequestException()
    
    response = client.delete('/api/links/lk_1')
    assert response.status_code == 503


def test_api_delete_link_unexpected_error(client, mock_link_service):
    """Verifica manejo de errores inesperados en DELETE /api/links/<id>."""
    mock_link_service.delete_link.side_effect = Exception("Error inesperado")
    
    response = client.delete('/api/links/lk_1')
    assert response.status_code == 500


# ============================================================================
# TESTS DE API ROUTES - GET /api/links/<link_id>/metrics
# ============================================================================

def test_api_metrics_success(client, mock_link_service):
    """Verifica obtención exitosa de métricas."""
    mock_link_service.get_link_metrics.return_value = {
        'totals': {'clicks': 100, 'byVariant': {'ig': 50}}
    }
    
    response = client.get('/api/links/lk_1/metrics')
    data = response.get_json()
    
    assert response.status_code == 200
    assert data['totals']['clicks'] == 100


def test_api_metrics_not_found(client, mock_link_service):
    """Verifica respuesta cuando no existen métricas."""
    mock_link_service.get_link_metrics.return_value = None
    
    response = client.get('/api/links/lk_inexistente/metrics')
    assert response.status_code == 404


def test_api_metrics_connection_error(client, mock_link_service):
    """Verifica manejo de errores de conexión en GET metrics."""
    mock_link_service.get_link_metrics.side_effect = requests.RequestException()
    
    response = client.get('/api/links/lk_1/metrics')
    assert response.status_code == 503


def test_api_metrics_unexpected_error(client, mock_link_service):
    """Verifica manejo de errores inesperados en GET metrics."""
    mock_link_service.get_link_metrics.side_effect = Exception("Error inesperado")
    
    response = client.get('/api/links/lk_1/metrics')
    assert response.status_code == 500


# ============================================================================
# TESTS DE API ROUTES - GET /api/health
# ============================================================================

def test_api_health_check_healthy(client, mock_link_service):
    """Verifica que /api/health responde con estructura esperada cuando todo está bien."""
    mock_link_service.health_check.return_value = True
    
    response = client.get('/api/health')
    data = response.get_json()
    
    assert response.status_code == 200
    assert data['ok'] is True
    assert data['frontend'] == 'healthy'
    assert data['msAdmin'] == 'healthy'


def test_api_health_check_admin_unhealthy(client, mock_link_service):
    """Verifica health check cuando MS Admin no está saludable."""
    mock_link_service.health_check.return_value = False
    
    response = client.get('/api/health')
    data = response.get_json()
    
    assert response.status_code == 200
    assert data['msAdmin'] == 'unhealthy'


def test_api_health_check_error(client, mock_link_service):
    """Verifica health check con error de conexión."""
    mock_link_service.health_check.side_effect = Exception("Connection error")
    
    response = client.get('/api/health')
    data = response.get_json()
    
    assert response.status_code == 503
    assert data['ok'] is False


# ============================================================================
# TESTS DEL LINK SERVICE
# ============================================================================

def test_link_service_init():
    """Verifica inicialización del servicio con URL del entorno."""
    with patch.dict('os.environ', {'ADMIN_API_URL': 'http://test-api:9000'}):
        from services.link_service import LinkService
        service = LinkService()
        assert service.admin_api_url == 'http://test-api:9000'


def test_link_service_strips_trailing_slash():
    """Verifica que se elimina la barra final de la URL."""
    with patch.dict('os.environ', {'ADMIN_API_URL': 'http://test-api:9000/'}):
        from services.link_service import LinkService
        service = LinkService()
        assert service.admin_api_url == 'http://test-api:9000'


def test_link_service_create_link_empty_title():
    """Verifica validación de título vacío."""
    from services.link_service import LinkService
    service = LinkService()
    
    with pytest.raises(ValueError, match='El título es requerido'):
        service.create_link('', 'slug', 'https://example.com', [])


def test_link_service_create_link_empty_slug():
    """Verifica validación de slug vacío."""
    from services.link_service import LinkService
    service = LinkService()
    
    with pytest.raises(ValueError, match='El slug es requerido'):
        service.create_link('Title', '', 'https://example.com', [])


def test_link_service_create_link_empty_url():
    """Verifica validación de URL vacía."""
    from services.link_service import LinkService
    service = LinkService()
    
    with pytest.raises(ValueError, match='La URL de destino es requerida'):
        service.create_link('Title', 'slug', '', [])


def test_link_service_create_link_invalid_slug():
    """Verifica validación de formato de slug."""
    from services.link_service import LinkService
    service = LinkService()
    
    with pytest.raises(ValueError, match='solo puede contener'):
        service.create_link('Title', 'INVALID-SLUG', 'https://example.com', [])


def test_link_service_create_link_slug_with_spaces():
    """Verifica que no se permiten espacios en el slug."""
    from services.link_service import LinkService
    service = LinkService()
    
    with pytest.raises(ValueError, match='solo puede contener'):
        service.create_link('Title', 'slug with spaces', 'https://example.com', [])


def test_link_service_create_link_backend_400_error():
    """Verifica manejo de error 400 del backend."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Error de validación'}
    
    with patch('requests.request', return_value=mock_response):
        with pytest.raises(ValueError, match='Error de validación'):
            service.create_link('Title', 'slug', 'https://example.com', [])


def test_link_service_create_link_backend_409_conflict():
    """Verifica manejo de error 409 (slug duplicado)."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 409
    
    with patch('requests.request', return_value=mock_response):
        with pytest.raises(ValueError, match='El slug ya existe'):
            service.create_link('Title', 'slug', 'https://example.com', [])


def test_link_service_create_link_backend_500_error():
    """Verifica manejo de error 500 del servidor."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 500
    
    with patch('requests.request', return_value=mock_response):
        with pytest.raises(ValueError, match='Error del servidor'):
            service.create_link('Title', 'slug', 'https://example.com', [])


def test_link_service_get_all_links_success():
    """Verifica obtención exitosa de links desde el servicio."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'items': [{'linkId': 'lk_1'}]}
    
    with patch('requests.request', return_value=mock_response):
        result = service.get_all_links()
        assert len(result) == 1


def test_link_service_get_all_links_empty():
    """Verifica respuesta vacía del servicio."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'items': []}
    
    with patch('requests.request', return_value=mock_response):
        result = service.get_all_links()
        assert result == []


def test_link_service_get_all_links_error_status():
    """Verifica manejo de errores en get_all_links."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 500
    
    with patch('requests.request', return_value=mock_response):
        result = service.get_all_links()
        assert result == []


def test_link_service_get_link_by_id_not_found():
    """Verifica respuesta cuando el link no existe."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch('requests.request', return_value=mock_response):
        result = service.get_link_by_id('lk_inexistente')
        assert result is None


def test_link_service_delete_link_success():
    """Verifica eliminación exitosa de un link."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 204
    
    with patch('requests.request', return_value=mock_response):
        result = service.delete_link('lk_1')
        assert result is True


def test_link_service_delete_link_not_found():
    """Verifica eliminación de link inexistente."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch('requests.request', return_value=mock_response):
        result = service.delete_link('lk_inexistente')
        assert result is False


def test_link_service_get_metrics_not_found():
    """Verifica obtención de métricas de link inexistente."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 404
    
    with patch('requests.request', return_value=mock_response):
        result = service.get_link_metrics('lk_inexistente')
        assert result is None


def test_link_service_health_check_healthy():
    """Verifica health check exitoso."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'ok': True}
    
    with patch('requests.request', return_value=mock_response):
        result = service.health_check()
        assert result is True


def test_link_service_health_check_unhealthy():
    """Verifica health check con servicio no saludable."""
    from services.link_service import LinkService
    service = LinkService()
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'ok': False}
    
    with patch('requests.request', return_value=mock_response):
        result = service.health_check()
        assert result is False


def test_link_service_health_check_error():
    """Verifica health check con error."""
    from services.link_service import LinkService
    service = LinkService()
    
    with patch('requests.request', side_effect=Exception()):
        result = service.health_check()
        assert result is False


def test_link_service_connection_error_in_create():
    """Verifica manejo de errores de conexión en create_link."""
    from services.link_service import LinkService
    service = LinkService()
    
    with patch('requests.request', side_effect=requests.RequestException()):
        with pytest.raises(requests.RequestException):
            service.create_link('Title', 'slug', 'https://example.com', [])


def test_link_service_unexpected_error_in_create():
    """Verifica manejo de errores inesperados en create_link."""
    from services.link_service import LinkService
    service = LinkService()
    
    with patch('requests.request', side_effect=Exception("Unexpected")):
        with pytest.raises(ValueError, match='Error al crear el link'):
            service.create_link('Title', 'slug', 'https://example.com', [])


# ============================================================================
# TESTS ADICIONALES PARA AUMENTAR COVERAGE (SERVICES Y RUTAS)
# ============================================================================

def test_link_service_make_request_connection_error(monkeypatch):
    """Verifica que _make_request propaga errores de conexión."""
    from services.link_service import LinkService
    service = LinkService()

    def mock_request(*args, **kwargs):
        raise requests.RequestException("Connection error")

    monkeypatch.setattr("requests.request", mock_request)

    with pytest.raises(requests.RequestException):
        service._make_request("GET", "/links")


def test_link_service_get_all_links_exception(monkeypatch):
    """Verifica manejo de excepciones inesperadas en get_all_links."""
    from services.link_service import LinkService
    service = LinkService()

    def mock_request(*args, **kwargs):
        raise Exception("Unexpected")

    monkeypatch.setattr("requests.request", mock_request)
    result = service.get_all_links()
    assert result == []


def test_link_service_get_link_by_id_exception(monkeypatch):
    """Verifica manejo de errores inesperados en get_link_by_id."""
    from services.link_service import LinkService
    service = LinkService()

    def mock_request(*args, **kwargs):
        raise Exception("Unexpected")

    monkeypatch.setattr("requests.request", mock_request)
    result = service.get_link_by_id("lk_test")
    assert result is None


def test_link_service_delete_link_exception(monkeypatch):
    """Verifica manejo de errores inesperados en delete_link."""
    from services.link_service import LinkService
    service = LinkService()

    def mock_request(*args, **kwargs):
        raise Exception("Unexpected")

    monkeypatch.setattr("requests.request", mock_request)
    result = service.delete_link("lk_test")
    assert result is False


def test_link_service_get_metrics_exception(monkeypatch):
    """Verifica manejo de errores inesperados en get_link_metrics."""
    from services.link_service import LinkService
    service = LinkService()

    def mock_request(*args, **kwargs):
        raise Exception("Unexpected")

    monkeypatch.setattr("requests.request", mock_request)
    result = service.get_link_metrics("lk_test")
    assert result is None


def test_link_service_health_check_request_exception(monkeypatch):
    """Verifica manejo de RequestException en health_check."""
    from services.link_service import LinkService
    service = LinkService()

    def mock_request(*args, **kwargs):
        raise requests.RequestException("Conn error")

    monkeypatch.setattr("requests.request", mock_request)
    result = service.health_check()
    assert result is False


def test_api_health_connection_error(client, mock_link_service):
    """Verifica que /api/health maneja excepciones."""
    mock_link_service.health_check.side_effect = requests.RequestException("error")
    response = client.get('/api/health')
    assert response.status_code in (503, 500)


def test_api_create_link_invalid_json(client):
    """Verifica que /api/links devuelve 400 si el JSON está malformado."""
    response = client.post('/api/links', data="not a json", content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
