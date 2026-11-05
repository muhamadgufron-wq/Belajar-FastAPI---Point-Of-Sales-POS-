def test_login_rate_limiting_triggers_429(client):
    """
    Memastikan proteksi brute-force aktif:
    Maksimal 5 percobaan request per menit per IP pada endpoint /auth/login.
    Percobaan ke-6 dari IP yang sama harus ditolak dengan 429 Too Many Requests.
    """
    attacker_ip = "192.0.2.100"
    headers = {"X-Forwarded-For": attacker_ip}
    payload = {"username": "kasir_pos", "password": "password_ngawur"}

    # 5 Percobaan pertama: masih diproses oleh backend (gagal karena password salah -> 401)
    for i in range(5):
        response = client.post("/auth/login", data=payload, headers=headers)
        assert response.status_code == 401, f"Percobaan ke-{i+1} seharusnya 401"

    # Percobaan ke-6: harus langsung dicegat oleh rate limiter (429 Too Many Requests)
    response_blocked = client.post("/auth/login", data=payload, headers=headers)
    assert response_blocked.status_code == 429
    data = response_blocked.json()
    assert "detail" in data
    assert "Terlalu banyak percobaan request" in data["detail"]
    assert "5 per 1 minute" in data["detail"]
    assert "retry-after" in response_blocked.headers


def test_rate_limiting_ip_isolation(client):
    """
    Memastikan rate limiting tidak memblokir IP lain:
    IP A yang terblokir tidak mempengaruhi IP B.
    """
    ip_a = "192.0.2.201"
    ip_b = "192.0.2.202"

    # Habiskan kuota IP A
    for _ in range(5):
        client.post(
            "/auth/login",
            data={"username": "kasir_pos", "password": "salah"},
            headers={"X-Forwarded-For": ip_a},
        )

    # Cek IP A terblokir (429)
    res_a = client.post(
        "/auth/login",
        data={"username": "kasir_pos", "password": "salah"},
        headers={"X-Forwarded-For": ip_a},
    )
    assert res_a.status_code == 429

    # IP B yang sah mencoba login: harus tetap bisa diproses dan berhasil login (200)
    res_b = client.post(
        "/auth/login",
        data={"username": "kasir_pos", "password": "mypassword123"},
        headers={"X-Forwarded-For": ip_b},
    )
    assert res_b.status_code == 200
    assert "access_token" in res_b.json()
