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
