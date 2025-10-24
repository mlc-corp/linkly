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
        
@patch("app.db.dynamo.boto3.Session")
def test_dynamo_initialization(mock_session):
    # Simula los objetos retornados por boto3
    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_session.return_value.resource.return_value = mock_resource

    # Importa el módulo después de aplicar el patch
    import importlib
    from app.db import dynamo
    importlib.reload(dynamo)  # fuerza la recarga con el mock activo

    # Verifica que la tabla haya sido creada correctamente
    mock_resource.Table.assert_called_once_with(dynamo.DDB_TABLE)
    assert dynamo.table == mock_table