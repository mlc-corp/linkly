import sys
import boto3
from botocore.config import Config
from app.core.config import settings

AWS_REGION = settings.AWS_REGION
DDB_TABLE = settings.DDB_TABLE
DDB_ENDPOINT = settings.DDB_ENDPOINT

if not DDB_TABLE:
    print("[linkly-ms] Falta DDB_TABLE en el entorno")
    sys.exit(1)

session = boto3.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)
config = Config(region_name=AWS_REGION)

if DDB_ENDPOINT:
    dynamodb = session.resource("dynamodb", endpoint_url=DDB_ENDPOINT, config=config)
else:
    dynamodb = session.resource("dynamodb", config=config)

table = dynamodb.Table(DDB_TABLE)
