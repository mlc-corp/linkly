import sys
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.client import Client

logger = logging.getLogger(__name__)

_db: Client = None

def get_db() -> Client:
    global _db
    if _db is None:
        try:
            logger.info("🔹 Inicializando cliente Firestore...")
            
            if not firebase_admin._DEFAULT_APP:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                logger.info("🔹 Firebase Admin App inicializada.")
            
            _db = firestore.client()
            logger.info("✅ Cliente Firestore conectado.")
            
        except Exception as e:
            logger.error(
                f"❌ ERROR CRÍTICO al inicializar Firestore: {e}",
                exc_info=True,
            )
            sys.exit(1)
    return _db

def check_firestore_connection():
    try:
        get_db()
        logger.info("✅ Verificación de conexión a Firestore exitosa.")
        return True
    except Exception as e:
        logger.error(f"❌ Verificación de conexión a Firestore fallida: {e}")
        return False
