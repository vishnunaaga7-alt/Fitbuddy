import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_fitbuddy.db")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "Generate 7-Day Plan" in response.text


def test_admin_requires_auth():
    response = client.get("/view-all-users")
    assert response.status_code == 401
