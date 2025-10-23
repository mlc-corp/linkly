# tests/test_smoke_linkly.py
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
import pytest


@pytest.fixture
def browser():
    """Configura el navegador en modo headless."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")           # Sin interfaz gráfica
    options.add_argument("--no-sandbox")         # Necesario para CI/CD
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_smoke_linkly(browser):
    """
    SMOKE TEST: Verifica la carga básica de Linkly.
    Este test se usa para confirmar que el frontend responde,
    renderiza correctamente y no arroja errores críticos.
    """
    # Leer la URL base del entorno (se configura en el pipeline)
    app_url = os.environ.get("APP_BASE_URL", "http://localhost:5000")
    print(f"Ejecutando smoke test contra: {app_url}")

    try:
        # Navegar a la app principal
        browser.get(app_url + "/app")

        # Verificar título de la página
        title = browser.title
        print(f"Título detectado: {title}")
        assert "Linkly" in title or "linkly" in title, "El título no contiene 'Linkly'"

        # Verificar encabezado principal (h1)
        h1_element = browser.find_element(By.TAG_NAME, "h1")
        print(f"Texto del encabezado H1: {h1_element.text}")
        assert "Linkly" in h1_element.text or "🔗" in h1_element.text, "No se encontró el encabezado principal"

        # Verificar texto de alguna sección principal
        page_source = browser.page_source
        assert "Crear Nuevo Link" in page_source, "El texto 'Crear Nuevo Link' no aparece en la página"

        print("Smoke test de Linkly pasado exitosamente.")

    except Exception as e:
        print(f"Smoke test falló: {e}")
        # Opcional: guardar captura para depurar en CI/CD
        # browser.save_screenshot('smoke_test_linkly_failure.png')
        raise
