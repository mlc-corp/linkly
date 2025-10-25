# tests/unit/test_template_rendering.py
"""
Pruebas unitarias para verificar el renderizado correcto de templates
y la estructura HTML generada.
"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app


class TestTemplateRendering:
    """Pruebas de renderizado de templates."""
    
    @pytest.fixture
    def client(self):
        """Fixture que retorna un cliente de prueba de Flask."""
        app = create_app()
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    # ============================================================================
    # TESTS DE TEMPLATE INDEX.HTML
    # ============================================================================
    
    def test_index_contains_form_elements(self, client):
        """Verifica que index.html contiene todos los elementos del formulario."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        
        # Verificar campos del formulario
        assert 'id="title"' in html
        assert 'id="slug"' in html
        assert 'id="destinationUrl"' in html
        assert 'id="variants"' in html
        assert 'id="linkForm"' in html
    
    def test_index_contains_message_container(self, client):
        """Verifica que existe el contenedor de mensajes."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'id="messageContainer"' in html
    
    def test_index_contains_links_table_container(self, client):
        """Verifica que existe el contenedor de la tabla de links."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'id="linksTableContainer"' in html
    
    def test_index_contains_help_texts(self, client):
        """Verifica que existen los textos de ayuda."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'help-text' in html
    
    def test_index_loads_correct_css(self, client):
        """Verifica que se cargan los archivos CSS correctos."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'css/style.css' in html
        assert 'css/index.css' in html
    
    def test_index_loads_correct_js(self, client):
        """Verifica que se carga el archivo JavaScript correcto."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'js/index.js' in html
    
    
    def test_index_form_has_submit_button(self, client):
        """Verifica que el formulario tiene botón de submit."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'type="submit"' in html
    
    def test_index_contains_sections(self, client):
        """Verifica que contiene las secciones principales."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'nuevo-link' in html
        assert 'links-section' in html
    
    # ============================================================================
    # TESTS DE TEMPLATE DETAIL.HTML
    # ============================================================================
    
    def test_detail_contains_link_id_input(self, client):
        """Verifica que detail.html contiene el input con el link_id."""
        response = client.get('/app/links/lk_test123')
        html = response.data.decode('utf-8')
        assert 'id="linkIdData"' in html
        assert 'value="lk_test123"' in html
    
    def test_detail_contains_content_container(self, client):
        """Verifica que existe el contenedor de contenido."""
        response = client.get('/app/links/lk_test123')
        html = response.data.decode('utf-8')
        assert 'id="contentContainer"' in html
    
    def test_detail_contains_back_button(self, client):
        """Verifica que existe el botón de regresar."""
        response = client.get('/app/links/lk_test123')
        html = response.data.decode('utf-8')
        assert 'btn-back' in html
        assert 'Volver' in html
    
    def test_detail_contains_header(self, client):
        """Verifica que existe el encabezado."""
        response = client.get('/app/links/lk_test123')
        html = response.data.decode('utf-8')
        assert 'Detalle del Link' in html
    
    def test_detail_loads_correct_css(self, client):
        """Verifica que se cargan los archivos CSS correctos."""
        response = client.get('/app/links/lk_test123')
        html = response.data.decode('utf-8')
        assert 'css/style.css' in html
        assert 'css/detail.css' in html
    
    def test_detail_loads_correct_js(self, client):
        """Verifica que se carga el archivo JavaScript correcto."""
        response = client.get('/app/links/lk_test123')
        html = response.data.decode('utf-8')
        assert 'js/detail.js' in html
    
    def test_detail_contains_base_domain_script(self, client):
        """Verifica que se establece la variable BASE_DOMAIN en JavaScript."""
        with patch.dict('os.environ', {'BASE_DOMAIN': 'http://test.com'}):
            response = client.get('/app/links/lk_test123')
            html = response.data.decode('utf-8')
            assert 'globalThis.BASE_DOMAIN' in html or 'BASE_DOMAIN' in html
    
    def test_detail_different_link_ids(self, client):
        """Verifica que diferentes link_ids se renderizan correctamente."""
        test_ids = ['lk_abc123', 'lk_xyz789', 'lk_test']
        
        for link_id in test_ids:
            response = client.get(f'/app/links/{link_id}')
            html = response.data.decode('utf-8')
            assert f'value="{link_id}"' in html
    
    def test_detail_loading_message(self, client):
        """Verifica que existe el mensaje de carga inicial."""
        response = client.get('/app/links/lk_test')
        html = response.data.decode('utf-8')
        assert 'loading' in html.lower() or 'cargando' in html.lower()
    
    # ============================================================================
    # TESTS DE ESTRUCTURA HTML GENERAL
    # ============================================================================
    
    def test_index_valid_html_structure(self, client):
        """Verifica que index.html tiene estructura HTML válida."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html
        assert '</body>' in html
        assert '</html>' in html
    
    def test_detail_valid_html_structure(self, client):
        """Verifica que detail.html tiene estructura HTML válida."""
        response = client.get('/app/links/lk_test')
        html = response.data.decode('utf-8')
        
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html
        assert '</body>' in html
        assert '</html>' in html
    
    def test_index_has_viewport_meta(self, client):
        """Verifica que tiene meta viewport para responsive."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'viewport' in html
        assert 'width=device-width' in html
    
    def test_detail_has_viewport_meta(self, client):
        """Verifica que detail tiene meta viewport."""
        response = client.get('/app/links/lk_test')
        html = response.data.decode('utf-8')
        assert 'viewport' in html
        assert 'width=device-width' in html
    
    def test_index_has_charset_meta(self, client):
        """Verifica que tiene definido el charset."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'charset' in html
        assert 'UTF-8' in html
    
    def test_detail_has_charset_meta(self, client):
        """Verifica que detail tiene charset."""
        response = client.get('/app/links/lk_test')
        html = response.data.decode('utf-8')
        assert 'charset' in html
        assert 'UTF-8' in html
    
    def test_index_has_title(self, client):
        """Verifica que tiene título."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert '<title>' in html
        assert 'Linkly' in html
    
    def test_detail_has_title(self, client):
        """Verifica que detail tiene título."""
        response = client.get('/app/links/lk_test')
        html = response.data.decode('utf-8')
        assert '<title>' in html
        assert 'Linkly' in html
    
    # ============================================================================
    # TESTS DE ACCESIBILIDAD
    # ============================================================================
    
    def test_index_form_labels_have_for_attribute(self, client):
        """Verifica que los labels tienen atributo for."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'for="title"' in html
        assert 'for="slug"' in html
        assert 'for="destinationUrl"' in html
    
    def test_index_inputs_have_required_attribute(self, client):
        """Verifica que los inputs requeridos tienen el atributo required."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'required' in html
    
    def test_index_has_placeholders(self, client):
        """Verifica que los inputs tienen placeholders."""
        response = client.get('/app')
        html = response.data.decode('utf-8')
        assert 'placeholder=' in html
    
    # ============================================================================
    # TESTS DE CSS
    # ============================================================================
    
    def test_static_css_files_exist(self, client):
        """Verifica que los archivos CSS existen y son accesibles."""
        css_files = [
            '/static/css/style.css',
            '/static/css/index.css',
            '/static/css/detail.css'
        ]
        
        for css_file in css_files:
            response = client.get(css_file)
            assert response.status_code == 200
            assert 'text/css' in response.content_type
    
    def test_style_css_contains_basic_rules(self, client):
        """Verifica que style.css contiene reglas básicas."""
        response = client.get('/static/css/style.css')
        css = response.data.decode('utf-8')
        
        assert 'body' in css or 'container' in css
        assert '{' in css
        assert '}' in css
    
    def test_index_css_contains_form_rules(self, client):
        """Verifica que index.css contiene reglas de formulario."""
        response = client.get('/static/css/index.css')
        css = response.data.decode('utf-8')
        
        assert 'form' in css.lower() or 'input' in css or 'button' in css
    
    def test_detail_css_contains_card_rules(self, client):
        """Verifica que detail.css contiene reglas de cards."""
        response = client.get('/static/css/detail.css')
        css = response.data.decode('utf-8')
        
        assert 'card' in css or 'container' in css or 'metric' in css
    
    # ============================================================================
    # TESTS DE JAVASCRIPT
    # ============================================================================
    
    def test_static_js_files_exist(self, client):
        """Verifica que los archivos JavaScript existen y son accesibles."""
        js_files = [
            '/static/js/index.js',
            '/static/js/detail.js'
        ]
        
        for js_file in js_files:
            response = client.get(js_file)
            assert response.status_code == 200
            # JavaScript puede ser text/javascript o application/javascript
            assert 'javascript' in response.content_type or 'plain' in response.content_type
    
    def test_index_js_contains_event_listeners(self, client):
        """Verifica que index.js contiene event listeners."""
        response = client.get('/static/js/index.js')
        js = response.data.decode('utf-8')
        
        assert 'addEventListener' in js or 'DOMContentLoaded' in js
    
    def test_index_js_contains_api_calls(self, client):
        """Verifica que index.js hace llamadas a la API."""
        response = client.get('/static/js/index.js')
        js = response.data.decode('utf-8')
        
        assert 'fetch' in js
    
    def test_detail_js_contains_api_calls(self, client):
        """Verifica que detail.js hace llamadas a la API."""
        response = client.get('/static/js/detail.js')
        js = response.data.decode('utf-8')
        
        assert 'fetch' in js
    
    def test_index_js_contains_functions(self, client):
        """Verifica que index.js contiene funciones definidas."""
        response = client.get('/static/js/index.js')
        js = response.data.decode('utf-8')
        
        # Buscar definiciones de función
        assert 'function' in js or 'async' in js or '=>' in js
    
    def test_detail_js_contains_functions(self, client):
        """Verifica que detail.js contiene funciones definidas."""
        response = client.get('/static/js/detail.js')
        js = response.data.decode('utf-8')
        
        # Buscar definiciones de función
        assert 'function' in js or 'async' in js or '=>' in js