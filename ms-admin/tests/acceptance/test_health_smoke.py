from fastapi.testclient import TestClient
from app.main import app 

client = TestClient(app)

def test_health_smoke():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"ok": True}
