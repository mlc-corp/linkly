import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_create_link():
    with patch("app.routes.links.create_link") as m:
        yield m


@pytest.fixture
def mock_list_links():
    with patch("app.routes.links.list_links") as m:
        yield m


@pytest.fixture
def mock_get_item():
    with patch("app.routes.links.get_item") as m:
        yield m


@pytest.fixture
def mock_delete_link():
    with patch("app.routes.links.delete_link") as m:
        yield m


@pytest.fixture
def mock_get_link_metrics():
    with patch("app.routes.links.get_link_metrics") as m:
        yield m


def test_create_link_endpoint(mock_create_link):
    mock_create_link.return_value = {
        "linkId": "lk_123",
        "slug": "test-link",
        "title": "Test",
        "destinationUrl": "http://example.com",
        "variants": ["default"],
        "createdAt": "2025-10-22T12:00:00Z",  
    }

    payload = {
        "title": "Test",
        "slug": "test-link",
        "destinationUrl": "http://example.com",
        "variants": ["default"],
    }

    response = client.post("/links", json=payload)
    assert response.status_code == 201
    assert response.json()["linkId"] == "lk_123"
    mock_create_link.assert_called_once()


def test_list_links_endpoint(mock_list_links):
    mock_list_links.return_value = [{"linkId": "lk_123"}]
    response = client.get("/links")
    assert response.status_code == 200
    assert response.json() == {"items": [{"linkId": "lk_123"}]}


def test_get_link_endpoint_found(mock_get_item):
    mock_get_item.return_value = {"linkId": "lk_123"}
    response = client.get("/links/lk_123")
    assert response.status_code == 200
    assert response.json() == {"linkId": "lk_123"}


def test_get_link_endpoint_not_found(mock_get_item):
    mock_get_item.return_value = None
    response = client.get("/links/lk_notfound")
    assert response.status_code == 404


def test_delete_link_endpoint(mock_delete_link):
    response = client.delete("/links/lk_123")
    assert response.status_code == 204
    mock_delete_link.assert_called_once_with("lk_123")


def test_get_metrics_endpoint(mock_get_link_metrics):
    mock_get_link_metrics.return_value = {"slug": "test", "totals": {"clicks": 10}}
    response = client.get("/links/lk_123/metrics")
    assert response.status_code == 200
    assert response.json()["totals"]["clicks"] == 10
