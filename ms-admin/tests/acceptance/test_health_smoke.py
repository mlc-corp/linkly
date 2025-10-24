import os
from fastapi.testclient import TestClient
from app.main import app

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

client = TestClient(app, base_url=BASE_URL)


def test_health_smoke():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"ok": True}
