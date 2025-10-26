import os
# --- CAMBIO ---
# Quita os y usa pydantic-settings para leer variables de entorno automáticamente
from pydantic_settings import BaseSettings
# -------------

# Define una clase que hereda de BaseSettings
class Settings(BaseSettings):
    # --- QUITAMOS LAS VARIABLES DE AWS ---
    # AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    # DDB_TABLE: str = os.getenv("DDB_TABLE", "LinklyTable-production")
    # DDB_ENDPOINT: str | None = os.getenv("DDB_ENDPOINT")
    # ------------------------------------

    # --- AÑADIMOS LAS VARIABLES DE FIRESTORE ---
    # pydantic-settings leerá estas variables del entorno (las que pone Terraform/Cloud Run).
    # Si no las encuentra, usará estos valores por defecto.
    LINKS_COLLECTION: str = "links"
    SLUGS_COLLECTION: str = "slugs"
    METRICS_COLLECTION: str = "metrics"
    # ------------------------------------------

    # Puedes añadir aquí otras configuraciones que necesites leer del entorno
    # Por ejemplo, si necesitaras el ID del proyecto en el código:
    # GCP_PROJECT_ID: str = "default-project-id"

    # Opcional: Configuración para leer desde un archivo .env localmente
    # model_config = SettingsConfigDict(env_file='.env', extra='ignore')

# Crea una instancia única de la configuración que tu app puede importar
settings = Settings()

# --- YA NO NECESITAS LA VERIFICACIÓN DE DDB_ENDPOINT ---
