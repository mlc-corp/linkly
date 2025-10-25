# app/core/config.py (o donde esté tu clase Settings)
import os

class Settings:
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DDB_TABLE: str = os.getenv("DDB_TABLE", "LinklyTable-production") # Asegúrate que el default sea correcto
    
    # --- CAMBIO ---
    # Si DDB_ENDPOINT no está, el default es None
    DDB_ENDPOINT: str | None = os.getenv("DDB_ENDPOINT") 
    # -------------
    
    # Ya no necesitas leer estas aquí si dynamo.py no las usa
    # AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "placeholder")
    # AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "placeholder")

settings = Settings()

# --- VERIFICACIÓN ADICIONAL en dynamo.py ---
# Asegúrate que la lógica que usa DDB_ENDPOINT sea robusta:
# (La versión que te di antes ya lo hace bien)
# if DDB_ENDPOINT: # Esto será falso si es None o ""
#    logger.warning(f"🔸 Usando endpoint DynamoDB LOCAL: {DDB_ENDPOINT}")
#    _dynamodb_resource = session.resource("dynamodb", endpoint_url=DDB_ENDPOINT, ...)
# else:
#    logger.info(f"🔹 Usando endpoint DynamoDB regional...")
#    _dynamodb_resource = session.resource("dynamodb", config=boto_config)