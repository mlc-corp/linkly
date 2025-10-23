import pytest
from unittest.mock import patch
from fastapi import HTTPException
from types import SimpleNamespace
from app.services import link_service, metrics_service

# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def sample_payload():
    return SimpleNamespace(
        slug=None,
        title="Test Link",
        destinationUrl="https://example.com",
        variants=["default"]
    )

# ---------------------------
# Link Service Tests
# ---------------------------
@patch("app.services.link_service.table")
def test_create_link_success(mock_table, sample_payload):
    mock_table.put_item.return_value = {}
    result = link_service.create_link(sample_payload)

    assert result["linkId"].startswith("lk_")
    assert result["slug"] == "test-link"
    assert result["title"] == "Test Link"
    mock_table.put_item.assert_called()

@patch("app.services.link_service.table")
def test_create_link_slug_conflict(mock_table, sample_payload):
    from botocore.exceptions import ClientError

    mock_table.put_item.side_effect = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
    )

    with pytest.raises(HTTPException) as exc:
        link_service.create_link(sample_payload)
    assert exc.value.status_code == 409

@patch("app.services.link_service.table")
def test_list_links(mock_table):
    mock_table.scan.return_value = {
        "Items": [
            {"PK": "LINK#lk_123", "SK": "META", "linkId": "lk_123", "slug": "test", "title": "Test", "destinationUrl": "url", "variants": ["default"], "createdAt": "2025-10-22T00:00:00Z"},
            {"PK": "LINK#lk_456", "SK": "OTHER"}  
        ]
    }
    result = link_service.list_links()
    assert len(result) == 1
    assert result[0]["slug"] == "test"

# ---------------------------
# Metrics Service Tests
# ---------------------------
@patch("app.services.metrics_service.table")
def test_get_link_by_id_success(mock_table):
    mock_table.get_item.return_value = {"Item": {"linkId": "lk_123", "slug": "test", "variants": ["default"]}}
    result = metrics_service.get_link_by_id("lk_123")
    assert result["linkId"] == "lk_123"

@patch("app.services.metrics_service.table")
def test_get_link_by_id_not_found(mock_table):
    mock_table.get_item.return_value = {}
    with pytest.raises(HTTPException) as exc:
        metrics_service.get_link_by_id("lk_123")
    assert exc.value.status_code == 404

@patch("app.services.metrics_service.get_link_by_id")
@patch("app.services.metrics_service.table")
def test_get_link_metrics(mock_table, mock_get_link):
    mock_get_link.return_value = {
        "linkId": "lk_123",
        "slug": "test",
        "variants": ["v1", "v2"]
    }
    mock_table.get_item.side_effect = [
        {"Item": {"clicks": 5, "byDevice": {"mobile": 3}, "byCountry": {"US": 5}}},
        {"Item": {"clicks": 2, "byDevice": {"desktop": 2}, "byCountry": {"US": 2}}}
    ]

    metrics = metrics_service.get_link_metrics("lk_123")
    assert metrics["totals"]["clicks"] == 7
    assert metrics["totals"]["byDevice"]["mobile"] == 3
    assert metrics["totals"]["byDevice"]["desktop"] == 2
    assert metrics["totals"]["byCountry"]["US"] == 7