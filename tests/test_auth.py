def test_root_endpoint(client):
    """Memastikan server aktif dan root endpoint merespons dengan benar."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Warung Umi Neneng" in data["app"]


def test_login_success_owner(client):
    """Memastikan user OWNER dapat login dan memperoleh JWT access token."""
    response = client.post(
        "/auth/login",
        data={"username": "kasir_pos", "password": "mypassword123"},
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_login_success_kasir(client):
    """Memastikan user KASIR dapat login dan memperoleh JWT access token."""
    response = client.post(
        "/auth/login",
        data={"username": "kasir_pos2", "password": "mypassword123"},
    )
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Memastikan login gagal (401) jika password salah."""
    response = client.post(
        "/auth/login",
        data={"username": "kasir_pos", "password": "password_salah_total"},
    )
    assert response.status_code == 401
    assert "Username atau password salah" in response.json()["detail"]


def test_login_user_not_found(client):
    """Memastikan login gagal (401) jika username tidak terdaftar."""
    response = client.post(
        "/auth/login",
        data={"username": "user_fiktif_12345", "password": "password123"},
    )
    assert response.status_code == 401


def test_get_current_user_me_owner(client, owner_headers):
    """Memastikan endpoint /auth/me mengembalikan profil OWNER secara akurat."""
    response = client.get("/auth/me", headers=owner_headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "kasir_pos"
    assert user_data["role"] == "OWNER"


def test_get_current_user_me_kasir(client, kasir_headers):
    """Memastikan endpoint /auth/me mengembalikan profil KASIR secara akurat."""
    response = client.get("/auth/me", headers=kasir_headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "kasir_pos2"
    assert user_data["role"] == "KASIR"


def test_get_current_user_unauthorized(client):
    """Memastikan endpoint terproteksi /auth/me menolak request tanpa token (401)."""
    response = client.get("/auth/me")
    assert response.status_code == 401
