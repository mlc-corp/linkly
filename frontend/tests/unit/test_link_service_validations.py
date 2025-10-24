# tests/unit/test_link_service_validations.py
"""
Pruebas unitarias enfocadas en validaciones y sanitización del LinkService.
Estas pruebas se enfocan en casos edge y validaciones específicas.
"""
import pytest
import sys
import os
from unittest.mock import patch, Mock
import requests

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.link_service import LinkService


class TestLinkServiceValidations:
    """Pruebas de validaciones del servicio de links."""
    
    @pytest.fixture
    def service(self):
        """Fixture que retorna una instancia del servicio."""
        return LinkService()
    
    # ============================================================================
    # TESTS DE SANITIZACIÓN DE IDs
    # ============================================================================
    
    def test_sanitize_id_valid_alphanumeric(self, service):
        """Verifica que IDs alfanuméricos válidos pasen la sanitización."""
        result = service._sanitize_id("lk_test123")
        assert result == "lk_test123"
    
    def test_sanitize_id_with_hyphens(self, service):
        """Verifica que IDs con guiones sean aceptados."""
        result = service._sanitize_id("lk-test-123")
        assert result == "lk-test-123"
    
    def test_sanitize_id_with_underscores(self, service):
        """Verifica que IDs con guiones bajos sean aceptados."""
        result = service._sanitize_id("lk_test_123")
        assert result == "lk_test_123"
    
    def test_sanitize_id_invalid_characters(self, service):
        """Verifica que IDs con caracteres inválidos sean rechazados."""
        with pytest.raises(ValueError, match="Identificador de link inválido"):
            service._sanitize_id("lk/test")
    
    def test_sanitize_id_with_spaces(self, service):
        """Verifica que IDs con espacios sean rechazados."""
        with pytest.raises(ValueError, match="Identificador de link inválido"):
            service._sanitize_id("lk test")
    
    def test_sanitize_id_with_special_chars(self, service):
        """Verifica que IDs con caracteres especiales sean rechazados."""
        with pytest.raises(ValueError, match="Identificador de link inválido"):
            service._sanitize_id("lk@test")
    
    def test_sanitize_id_not_string(self, service):
        """Verifica que IDs no string sean rechazados."""
        with pytest.raises(ValueError, match="debe ser texto"):
            service._sanitize_id(12345)
    
    def test_sanitize_id_empty_string(self, service):
        """Verifica que strings vacíos sean rechazados."""
        with pytest.raises(ValueError, match="Identificador de link inválido"):
            service._sanitize_id("")
    
    # ============================================================================
    # TESTS DE VALIDACIÓN DE TÍTULO
    # ============================================================================
    
    def test_create_link_title_only_whitespace(self, service):
        """Verifica que títulos con solo espacios sean rechazados."""
        with pytest.raises(ValueError, match="El título es requerido"):
            service.create_link("   ", "slug", "https://example.com", [])
    
    def test_create_link_title_with_leading_trailing_spaces(self, service):
        """Verifica que se manejen correctamente títulos con espacios al inicio/final."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'slug': 'test',
            'title': 'Test Title'
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link("  Test Title  ", "test", "https://example.com", [])
            assert result['title'] == 'Test Title'
    
    # ============================================================================
    # TESTS DE VALIDACIÓN DE SLUG
    # ============================================================================
    
    def test_create_link_slug_only_whitespace(self, service):
        """Verifica que slugs con solo espacios sean rechazados."""
        with pytest.raises(ValueError, match="El slug es requerido"):
            service.create_link("Title", "   ", "https://example.com", [])
    
    def test_create_link_slug_with_uppercase(self, service):
        """Verifica que slugs con mayúsculas sean rechazados."""
        with pytest.raises(ValueError, match="solo puede contener"):
            service.create_link("Title", "Test-Slug", "https://example.com", [])
    
    def test_create_link_slug_with_underscores(self, service):
        """Verifica que slugs con guiones bajos sean rechazados."""
        with pytest.raises(ValueError, match="solo puede contener"):
            service.create_link("Title", "test_slug", "https://example.com", [])
    
    def test_create_link_slug_with_special_characters(self, service):
        """Verifica que slugs con caracteres especiales sean rechazados."""
        with pytest.raises(ValueError, match="solo puede contener"):
            service.create_link("Title", "test@slug", "https://example.com", [])
    
    def test_create_link_slug_valid_lowercase(self, service):
        """Verifica que slugs válidos en minúsculas sean aceptados."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'slug': 'valid-slug-123'
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link("Title", "valid-slug-123", "https://example.com", [])
            assert result['slug'] == 'valid-slug-123'
    
    def test_create_link_slug_with_numbers(self, service):
        """Verifica que slugs con números sean aceptados."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'slug': 'test2025'
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link("Title", "test2025", "https://example.com", [])
            assert result['slug'] == 'test2025'
    
    # ============================================================================
    # TESTS DE VALIDACIÓN DE URL
    # ============================================================================
    
    def test_create_link_url_only_whitespace(self, service):
        """Verifica que URLs con solo espacios sean rechazadas."""
        with pytest.raises(ValueError, match="La URL de destino es requerida"):
            service.create_link("Title", "slug", "   ", [])
    
    def test_create_link_url_with_spaces(self, service):
        """Verifica que se manejen correctamente URLs con espacios."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'destinationUrl': 'https://example.com'
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link(
                "Title", 
                "slug", 
                "  https://example.com  ", 
                []
            )
            assert result['destinationUrl'] == 'https://example.com'
    
    # ============================================================================
    # TESTS DE VALIDACIÓN DE VARIANTES
    # ============================================================================
    
    def test_create_link_variants_empty_list(self, service):
        """Verifica que listas vacías de variantes sean manejadas correctamente."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'variants': []
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link("Title", "slug", "https://example.com", [])
            assert result['variants'] == []
    
    def test_create_link_variants_none(self, service):
        """Verifica que None como variantes sea manejado correctamente."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'variants': []
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link("Title", "slug", "https://example.com", None)
            assert result['variants'] == []
    
    def test_create_link_variants_with_values(self, service):
        """Verifica que variantes con valores sean enviadas correctamente."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'linkId': 'lk_test',
            'variants': ['ig', 'facebook', 'twitter']
        }
        
        with patch('requests.request', return_value=mock_response):
            result = service.create_link(
                "Title", 
                "slug", 
                "https://example.com", 
                ['ig', 'facebook', 'twitter']
            )
            assert len(result['variants']) == 3
    
    # ============================================================================
    # TESTS DE MANEJO DE RESPUESTAS DEL BACKEND
    # ============================================================================
    
    def test_create_link_backend_400_with_custom_message(self, service):
        """Verifica manejo de error 400 con mensaje personalizado."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Slug inválido'}
        
        with patch('requests.request', return_value=mock_response):
            with pytest.raises(ValueError, match='Slug inválido'):
                service.create_link("Title", "slug", "https://example.com", [])
    
    def test_create_link_backend_400_without_error_message(self, service):
        """Verifica manejo de error 400 sin mensaje de error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {}
        
        with patch('requests.request', return_value=mock_response):
            with pytest.raises(ValueError, match='Error de validación'):
                service.create_link("Title", "slug", "https://example.com", [])
    
    def test_get_link_by_id_error_status(self, service):
        """Verifica manejo de códigos de error diferentes a 404."""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('requests.request', return_value=mock_response):
            result = service.get_link_by_id("lk_test")
            assert result is None
    
    def test_delete_link_error_status(self, service):
        """Verifica manejo de códigos de error en delete."""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('requests.request', return_value=mock_response):
            result = service.delete_link("lk_test")
            assert result is False
    
    def test_get_metrics_error_status(self, service):
        """Verifica manejo de códigos de error en get_metrics."""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('requests.request', return_value=mock_response):
            result = service.get_link_metrics("lk_test")
            assert result is None
    
    # ============================================================================
    # TESTS DE TIMEOUT Y CONFIGURACIÓN
    # ============================================================================
    
    def test_make_request_includes_timeout(self, service):
        """Verifica que las peticiones incluyan timeout."""
        mock_request = Mock(return_value=Mock(status_code=200))
        
        with patch('requests.request', mock_request):
            service._make_request('GET', '/test')
            
            # Verificar que se llamó con timeout
            call_kwargs = mock_request.call_args[1]
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] == 10
    
    def test_service_strips_multiple_trailing_slashes(self):
        """Verifica que se eliminen múltiples barras finales."""
        with patch.dict('os.environ', {'ADMIN_API_URL': 'http://test-api:9000///'}):
            service = LinkService()
            assert service.admin_api_url == 'http://test-api:9000'
    
    # ============================================================================
    # TESTS DE EDGE CASES
    # ============================================================================
    
    def test_health_check_with_invalid_response(self, service):
        """Verifica health check con respuesta inválida."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Sin campo 'ok'
        
        with patch('requests.request', return_value=mock_response):
            result = service.health_check()
            assert result is False
    
    def test_get_all_links_missing_items_key(self, service):
        """Verifica manejo cuando falta la clave 'items' en la respuesta."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Sin 'items'
        
        with patch('requests.request', return_value=mock_response):
            result = service.get_all_links()
            assert result == []