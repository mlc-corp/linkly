import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")


@pytest.fixture
def browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_homepage_loads(browser):
    # Carga de página principal
    browser.get(BASE_URL + "/app")

    try:
        title = WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        assert "Linkly" in title.text
    except TimeoutException:
        pytest.fail("No se cargó correctamente la página principal.")


def test_create_new_link(browser):
    # Creación de un nuevo link
    browser.get(BASE_URL + "/app")

    # Esperar el formulario
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "linkForm"))
    )

    # Rellenar campos del formulario
    browser.find_element(By.ID, "title").send_keys("Evento 2025 Test")
    browser.find_element(By.ID, "slug").send_keys("evento2025test")
    browser.find_element(By.ID, "destinationUrl").send_keys("https://myevent.com")
    browser.find_element(By.ID, "variants").send_keys("ig, facebook, x")

    # Enviar formulario
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Esperar mensaje o redirección
    try:
        message = WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.ID, "messageContainer"))
        )
        assert "creado" in message.text.lower() or "éxito" in message.text.lower()
    except TimeoutException:
        pytest.fail("No apareció mensaje de confirmación de creación del link.")


def test_link_appears_in_list(browser):
    # Verificar que el nuevo link aparezca en la lista
    browser.get(BASE_URL + "/app")

    # Esperar a que el contenedor se cargue
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "linksTableContainer"))
    )

    # Esperar dinámicamente hasta que el slug "evento2025test" aparezca en el DOM
    try:
        text_found = WebDriverWait(browser, 10).until(
            EC.text_to_be_present_in_element(
                (By.ID, "linksTableContainer"),
                "evento2025test"
            )
        )
        assert text_found, "El texto 'evento2025test' no apareció en el DOM."
    except TimeoutException:
        html = browser.page_source
        print("\n[DEBUG] Contenido actual del linksTableContainer:\n", html[:500])
        pytest.fail("El nuevo link no aparece en la lista de links (timeout esperando que JS lo renderice).")


def test_link_detail_loads(browser):
    # Ingresar al detalle de un link y verificar carga de métricas
    link_id = os.environ.get("TEST_LINK_ID", "lk_test_id")

    browser.get(BASE_URL + f"/app/links/{link_id}")

    try:
        header = WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        assert "Detalle del Link" in header.text
    except TimeoutException:
        pytest.fail("No se cargó la página de detalle del link.")

    # Verificar carga de métricas simuladas
    container = browser.find_element(By.ID, "contentContainer")
    assert container is not None, "No se encontró contenedor de métricas en la vista detalle."
