def test_cors_trusted_origin_simple_request(client):
    """Origin terpercaya (http://localhost:5173) mendapatkan header Access-Control-Allow-Origin."""
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_untrusted_origin_blocked(client):
    """Origin tidak dikenal (http://evil-site.com) TIDAK diberikan header Access-Control-Allow-Origin."""
    response = client.get("/", headers={"Origin": "http://evil-site.com"})
    assert response.status_code == 200
    # Browser akan memblokir respon ini karena header allow-origin tidak ada
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_preflight_options_request(client):
    """Browser mengirim preflight OPTIONS sebelum request mutasi (POST/PATCH/DELETE) berizin."""
    response = client.options(
        "/transactions/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
    assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()


def test_cors_preflight_untrusted_blocked(client):
    """Preflight OPTIONS dari domain jahat ditolak oleh backend (tidak diberi izin)."""
    response = client.options(
        "/transactions/",
        headers={
            "Origin": "http://attacker-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.headers.get("access-control-allow-origin") is None
