import sys
import boto3
from botocore.config import Config
from app.core.config import settings

# Variables base
AWS_REGION = settings.AWS_REGION
DDB_TABLE = settings.DDB_TABLE

if not DDB_TABLE:
    print("[linkly-ms] ❌ Falta DDB_TABLE en el entorno")
    sys.exit(1)

# Configuración global de boto3
config = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "standard"},
    read_timeout=3,
    connect_timeout=1,
)

# ✅ No pasamos credenciales ni endpoint_url: boto3 las detecta automáticamente
# - En local: usa las del entorno (~/.aws/credentials o env vars)
# - En ECS: usa las credenciales temporales del Task Role (LabRoleArn)
session = boto3.Session(region_name=AWS_REGION)
dynamodb = session.resource("dynamodb", config=config)

# Referencia a la tabla
table = dynamodb.Table(DDB_TABLE)

print(f"[linkly-ms] ✅ Conectado a DynamoDB (tabla={DDB_TABLE}, región={AWS_REGION})")
