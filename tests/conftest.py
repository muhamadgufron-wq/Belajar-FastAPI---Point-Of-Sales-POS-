import pytest
from fastapi.testclient import TestClient

from app.core.limiter import limiter
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Mereset rate limiter sebelum dan sesudah setiap test agar isolasi terjaga."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(scope="session")
def client():
    """Fixture TestClient utama untuk menjalankan request API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def owner_headers(client):
    """Fixture token otentikasi untuk role OWNER (kasir_pos)."""
    res = client.post(
        "/auth/login",
        data={"username": "kasir_pos", "password": "mypassword123"},
    )
    assert res.status_code == 200, f"Gagal login sebagai OWNER: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def kasir_headers(client):
    """Fixture token otentikasi untuk role KASIR (kasir_pos2)."""
    res = client.post(
        "/auth/login",
        data={"username": "kasir_pos2", "password": "mypassword123"},
    )
    assert res.status_code == 200, f"Gagal login sebagai KASIR: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
