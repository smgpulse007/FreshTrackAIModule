from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_process_receipt():
    with open("tests/sample_receipt.jpg", "rb") as file:
        response = client.post("/api/v1/process_receipt", files={"file": file})
    assert response.status_code == 200
    assert "items" in response.json()

def test_process_receipt_invalid_file():
    response = client.post("/api/v1/process_receipt", files={"file": ("invalid.txt", b"invalid content")})
    assert response.status_code == 400
    assert "detail" in response.json()

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}