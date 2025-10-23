import os

class Settings:
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DDB_TABLE: str = os.getenv("DDB_TABLE", "LinklyTable")
    DDB_ENDPOINT: str = os.getenv("DDB_ENDPOINT", "http://localhost:8000")

settings = Settings()