import os


class Settings:
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DDB_TABLE: str = os.getenv("DDB_TABLE", "LinklyTable")
    DDB_ENDPOINT: str = os.getenv("DDB_ENDPOINT", "http://localhost:8000")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "placeholder")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "placeholder")


settings = Settings()
