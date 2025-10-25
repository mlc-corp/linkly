import pytest
from unittest.mock import patch, MagicMock
import importlib

# Importa el módulo que quieres probar
from app.db import dynamo

# Resetea los singletons internos del módulo dynamo antes de cada test
# para asegurar aislamiento entre pruebas.
@pytest.fixture(autouse=True)
def reset_dynamo_singletons():
    dynamo._dynamodb_resource = None
    dynamo._table = None
    yield # Deja que el test corra
    dynamo._dynamodb_resource = None
    dynamo._table = None


@patch("app.db.dynamo.boto3.Session")
def test_get_table_initialization_local(mock_boto_session_cls, monkeypatch):
    """
    Verifica que get_table inicializa correctamente la conexión LOCAL
    cuando DDB_ENDPOINT SÍ está definido.
    """
    # Configura mocks (igual que antes)
    mock_session_instance = MagicMock()
    mock_resource_instance = MagicMock()
    mock_table_instance = MagicMock()
    mock_boto_session_cls.return_value = mock_session_instance
    mock_session_instance.resource.return_value = mock_resource_instance
    mock_resource_instance.Table.return_value = mock_table_instance

    # Define un endpoint local para este test
    local_endpoint = "http://localhost:8000"
    monkeypatch.setattr(dynamo.settings, "DDB_ENDPOINT", local_endpoint, raising=False)
    monkeypatch.setattr(dynamo, "DDB_TABLE", "TestTableLocal", raising=False)
    # importlib.reload(dynamo)

    # --- Llama a la función ---
    table_result = dynamo.get_table()

    # --- Verificaciones ---
    mock_boto_session_cls.assert_called_once_with(region_name=dynamo.AWS_REGION)
    
    # Verifica que se llamó a resource con endpoint_url
    mock_session_instance.resource.assert_called_once_with("dynamodb", 
                                                          endpoint_url=local_endpoint, 
                                                          config=dynamo.boto_config)
                                                          
    mock_resource_instance.Table.assert_called_once_with("TestTableLocal")
    assert table_result == mock_table_instance


def test_get_table_missing_env_var(monkeypatch):
    """
    Verifica que get_table llama a sys.exit si DDB_TABLE no está definida.
    """
    # Simula que DDB_TABLE no está definida
    monkeypatch.setattr(dynamo, "DDB_TABLE", None, raising=False)
    # importlib.reload(dynamo) # Recarga para que tome el valor None
    
    # Verifica que llamar a get_table causa SystemExit
    with pytest.raises(SystemExit) as excinfo:
        dynamo.get_table()
    # Verifica que el código de salida sea 1
    assert excinfo.value.code == 1
