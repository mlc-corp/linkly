import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_boto3_session():
    with patch("boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_resource = MagicMock()
        mock_table = MagicMock()

        mock_session_cls.return_value = mock_session
        mock_session.resource.return_value = mock_resource
        mock_resource.Table.return_value = mock_table

        yield mock_session, mock_resource, mock_table

def test_dynamo_initialization(mock_boto3_session):
    from app.db import dynamo

    mock_session, mock_resource, mock_table = mock_boto3_session

    assert dynamo.table == mock_table

    mock_session.resource.assert_called_once()
    mock_resource.Table.assert_called_once()