import pytest
from unittest.mock import patch
from fastapi import HTTPException
from types import SimpleNamespace
from app.services import link_service, metrics_service
from botocore.exceptions import ClientError


# ---------------------------
# Fixtures
# ---------------------------
@pytest.fixture
def sample_payload():
    return SimpleNamespace(
        slug=None,
        title="Test Link",
        destinationUrl="https://example.com",
        variants=["default"],
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
def test_create_link_without_title(mock_table, sample_payload):
    sample_payload.title = ""
    with pytest.raises(HTTPException) as exc:
        link_service.create_link(sample_payload)
    assert exc.value.status_code == 400


@patch("app.services.link_service.table")
def test_create_link_client_error_meta(mock_table, sample_payload):
    from botocore.exceptions import ClientError

    mock_table.put_item.side_effect = ClientError(
        {"Error": {"Code": "SomeOtherException"}}, "PutItem"
    )
    with pytest.raises(HTTPException) as exc:
        link_service.create_link(sample_payload)
    assert exc.value.status_code == 500


@patch("app.services.link_service.table")
def test_create_link_slug_exists(mock_table, sample_payload):
    def put_item_side_effect(Item, ConditionExpression=None):
        # maestro siempre OK
        if Item["SK"] == "META" and not Item["PK"].endswith(Item["linkId"]):
            # alias falla por slug duplicado
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
            )
        return {}

    mock_table.put_item.side_effect = put_item_side_effect

    # Se espera que se lance HTTPException 409
    with pytest.raises(link_service.HTTPException) as exc:
        link_service.create_link(sample_payload)

    assert exc.value.status_code == 409
    assert exc.value.detail == "El slug ya existe"


# ---------------------------
# List Links Tests
# ---------------------------
@patch("app.services.link_service.table")
def test_list_links(mock_table):
    mock_table.scan.return_value = {
        "Items": [
            {
                "PK": "LINK#lk_123",
                "SK": "META",
                "linkId": "lk_123",
                "slug": "test",
                "title": "Test",
                "destinationUrl": "url",
                "variants": ["default"],
                "createdAt": "2025-10-22T00:00:00Z",
            },
            {"PK": "LINK#lk_456", "SK": "OTHER"},
        ]
    }
    result = link_service.list_links()
    assert len(result) == 1
    assert result[0]["slug"] == "test"


@patch("app.services.link_service.table")
def test_list_links_filtered(mock_table):
    mock_table.scan.return_value = {
        "Items": [
            {
                "PK": "LINK#lk_001",
                "SK": "META",
                "linkId": "lk_001",
                "slug": "a",
                "title": "A",
                "destinationUrl": "url",
                "variants": ["default"],
                "createdAt": "2025-10-22T00:00:00Z",
            },
            {
                "PK": "LINK#lk_002",
                "SK": "META",
                "linkId": "lk_002",
                "slug": "b",
                "title": "B",
                "destinationUrl": "url",
                "variants": ["default"],
                "createdAt": "2025-10-22T00:00:00Z",
            },
            {"PK": "LINK#lk_002", "SK": "OTHER"},
        ]
    }
    result = link_service.list_links()
    assert len(result) == 2


# ---------------------------
# Delete Link Tests
# ---------------------------
@patch("app.services.link_service.get_item")
@patch("app.services.link_service.table")
def test_delete_link_success(mock_table, mock_get_item):
    mock_get_item.return_value = {"linkId": "lk_123", "slug": "test"}
    mock_table.delete_item.return_value = {}
    link_service.delete_link("lk_123")
    assert mock_table.delete_item.call_count == 2


@patch("app.services.link_service.get_item")
def test_delete_link_not_found(mock_get_item):
    mock_get_item.return_value = None
    with pytest.raises(HTTPException) as exc:
        link_service.delete_link("lk_123")
    assert exc.value.status_code == 404


@patch("app.services.link_service.get_item")
@patch("app.services.link_service.table")
def test_delete_link_client_error(mock_table, mock_get_item):
    mock_get_item.return_value = {"linkId": "lk_123", "slug": "test"}
    mock_table.delete_item.side_effect = Exception("DB error")
    with pytest.raises(Exception):
        link_service.delete_link("lk_123")


# ---------------------------
# Metrics Service Tests
# ---------------------------
@patch("app.services.metrics_service.table")
def test_get_link_by_id_success(mock_table):
    mock_table.get_item.return_value = {
        "Item": {"linkId": "lk_123", "slug": "test", "variants": ["default"]}
    }
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
        "variants": ["v1", "v2"],
    }
    mock_table.get_item.side_effect = [
        {"Item": {"clicks": 5, "byDevice": {"mobile": 3}, "byCountry": {"US": 5}}},
        {"Item": {"clicks": 2, "byDevice": {"desktop": 2}, "byCountry": {"US": 2}}},
    ]

    metrics = metrics_service.get_link_metrics("lk_123")
    assert metrics["totals"]["clicks"] == 7
    assert metrics["totals"]["byDevice"]["mobile"] == 3
    assert metrics["totals"]["byDevice"]["desktop"] == 2
    assert metrics["totals"]["byCountry"]["US"] == 7
