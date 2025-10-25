import sys
import boto3
import logging
from botocore.config import Config

# Asegúrate que esta ruta de import sea correcta para tu proyecto
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Variables de Configuración (Leídas al inicio) ---
AWS_REGION = settings.AWS_REGION
DDB_TABLE = settings.DDB_TABLE
# DDB_ENDPOINT solo se usa si está definido (para local/testing)
DDB_ENDPOINT = settings.DDB_ENDPOINT

if not DDB_TABLE:
    logger.error("❌ Falta DDB_TABLE en el entorno")
    sys.exit(1)

# Configuración global de boto3 (Timeouts, Retries)
boto_config = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "standard"},
    read_timeout=3,  # Timeout de lectura en segundos
    connect_timeout=1,  # Timeout de conexión en segundos
)

# --- Variables Globales para Caching (Lazy Initialization) ---
_dynamodb_resource = None
_table = None


# --- Función para obtener el Recurso DynamoDB (Lazy) ---
def get_dynamodb_resource():
    """Crea o devuelve la instancia singleton del recurso DynamoDB."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        logger.info(f"🔹 Inicializando recurso DynamoDB para región {AWS_REGION}...")

        # Usa credenciales del rol IAM automáticamente (NO pasar keys)
        session = boto3.Session(region_name=AWS_REGION)

        if DDB_ENDPOINT:
            logger.warning(f"🔸 Usando endpoint DynamoDB LOCAL: {DDB_ENDPOINT}")
            _dynamodb_resource = session.resource(
                "dynamodb", endpoint_url=DDB_ENDPOINT, config=boto_config
            )
        else:
            logger.info(f"🔹 Usando endpoint DynamoDB regional para {AWS_REGION}")
            _dynamodb_resource = session.resource("dynamodb", config=boto_config)
    return _dynamodb_resource


# --- Función para obtener la Tabla (Lazy) ---
def get_table():
    """Crea o devuelve la instancia singleton de la tabla DynamoDB."""
    global _table
    if _table is None:
        logger.info(f"🔹 Obteniendo referencia a la tabla DynamoDB: {DDB_TABLE}")
        try:
            dynamodb = get_dynamodb_resource()
            _table = dynamodb.Table(DDB_TABLE)
            # Opcional: Llamada para verificar conexión/permisos al inicio.
            # Puede ralentizar el primer request. Boto3 lo hará 'lazy' si no lo llamas.
            # logger.info("🔹 Verificando acceso a la tabla...")
            # _table.load()
            # logger.info("✅ Acceso a la tabla verificado.")
            logger.info(f"✅ Referencia a la tabla {DDB_TABLE} obtenida.")
        except Exception as e:
            logger.error(
                f"❌ ERROR CRÍTICO al obtener/verificar la tabla DynamoDB '{DDB_TABLE}': {e}",
                exc_info=True,
            )
            # Considera lanzar una excepción personalizada en lugar de sys.exit
            # para que FastAPI pueda manejarlo como un error 500.
            # raise RuntimeError(f"No se pudo conectar a la tabla {DDB_TABLE}") from e
            sys.exit(1)  # O mantener sys.exit si prefieres que el contenedor falle
    return _table


# --- NO CREAR LA TABLA AQUÍ ---
# table = get_table() # <-- Esto NO se hace a nivel de módulo


# Puedes añadir una función de health check si quieres
def check_dynamodb_connection():
    """Intenta obtener la tabla para verificar la conexión."""
    try:
        get_table()  # Intenta inicializar la conexión si no lo ha hecho
        # Podrías añadir una operación de bajo impacto como describe_table si es necesario
        logger.info("✅ Verificación de conexión a DynamoDB exitosa.")
        return True
    except Exception as e:
        logger.error(f"❌ Verificación de conexión a DynamoDB fallida: {e}")
        return False
