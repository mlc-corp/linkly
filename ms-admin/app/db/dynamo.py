import sys
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client # Mantener por si acaso, aunque no lo usemos directo
# --- AÑADIDO: Importar el cliente ASÍNCRONO ---
from google.cloud.firestore_v1.async_client import AsyncClient
# ----------------------------------------------

logger = logging.getLogger(__name__)

# --- CAMBIO: Variable para cliente asíncrono ---
_async_db: AsyncClient = None
# ---------------------------------------------

def initialize_firebase():
    """Inicializa la app Firebase Admin si no existe."""
    # --- CAMBIO: Forma correcta de verificar si ya está inicializado ---
    try:
        # Intenta obtener la app por defecto. Si no existe, lanza ValueError.
        firebase_admin.get_app()
        logger.info("🔹 Firebase Admin App ya estaba inicializada.")
    except ValueError:
        # Si no está inicializada, la inicializamos
        try:
            logger.info("🔹 Inicializando Firebase Admin App con credenciales por defecto...")
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin App inicializada.")
        except Exception as e:
            logger.error(
                f"❌ ERROR CRÍTICO al inicializar Firebase Admin: {e}",
                exc_info=True,
            )
            # Es mejor lanzar una excepción aquí para que FastAPI la maneje
            raise RuntimeError(f"No se pudo inicializar Firebase Admin: {e}") from e
    # -----------------------------------------------------------------

# --- CAMBIO: Devolver Cliente Asíncrono ---
def get_db() -> AsyncClient:
    """Obtiene la instancia singleton del cliente Async Firestore."""
    global _async_db
    if _async_db is None:
        try:
            initialize_firebase() # Asegura que la app esté lista
            logger.info("🔹 Obteniendo cliente Async Firestore...")
            # --- CAMBIO: Usar firestore.aio.client() ---
            _async_db = firestore.aio.client()
            # -----------------------------------------
            logger.info("✅ Cliente Async Firestore conectado.")

        except Exception as e:
            logger.error(
                f"❌ ERROR CRÍTICO al obtener cliente Async Firestore: {e}",
                exc_info=True,
            )
            # Salir aquí puede ser muy drástico, mejor lanzar excepción
            # sys.exit(1)
            raise RuntimeError(f"No se pudo obtener cliente Firestore: {e}") from e
    return _async_db
# -----------------------------------------

def check_firestore_connection():
    """Verifica si se puede obtener una conexión a Firestore."""
    try:
        get_db() # Intenta inicializar y obtener el cliente async
        # Podrías añadir una lectura simple aquí si quieres probar más a fondo
        logger.info("✅ Verificación de conexión a Firestore exitosa.")
        return True
    except Exception as e:
        logger.error(f"❌ Verificación de conexión a Firestore fallida: {e}", exc_info=True)
        return False
