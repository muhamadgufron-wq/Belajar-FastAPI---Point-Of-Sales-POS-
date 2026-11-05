def test_kasir_can_view_products(client, kasir_headers):
    """KASIR diizinkan melihat katalog produk untuk operasional toko."""
    response = client.get("/products/", headers=kasir_headers)
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert "meta" in json_data


def test_kasir_cannot_create_product(client, kasir_headers):
    """KASIR dilarang menambah produk baru (harus 403 Forbidden)."""
    payload = {
        "name": "Barang Ilegal Kasir",
        "harga_modal": 1000,
        "harga_jual": 2000,
        "stock": 10,
    }
    response = client.post("/products/", headers=kasir_headers, json=payload)
    assert response.status_code == 403


def test_kasir_cannot_update_product(client, kasir_headers):
    """KASIR dilarang mengedit produk (harus 403 Forbidden)."""
    response = client.patch(
        "/products/1",
        headers=kasir_headers,
        json={"name": "Ganti Nama Oleh Kasir"},
    )
    assert response.status_code == 403


def test_kasir_cannot_delete_product(client, kasir_headers):
    """KASIR dilarang menghapus produk (harus 403 Forbidden)."""
    response = client.delete("/products/1", headers=kasir_headers)
    assert response.status_code == 403


def test_owner_crud_product_lifecycle(client, owner_headers):
    """Siklus lengkap CRUD produk oleh OWNER: Create, Read, Update, Delete (Soft)."""
    # 1. CREATE
    create_payload = {
        "name": "Teh Pucuk Harum 350ml",
        "harga_modal": 2500.0,
        "harga_jual": 3500.0,
        "stock": 24,
    }
    res_create = client.post("/products/", headers=owner_headers, json=create_payload)
    assert res_create.status_code == 201
    prod = res_create.json()
    prod_id = prod["id"]
    assert prod["name"] == "Teh Pucuk Harum 350ml"
    assert prod["stock"] == 24

    # 2. READ DETAIL
    res_read = client.get(f"/products/{prod_id}", headers=owner_headers)
    assert res_read.status_code == 200
    assert res_read.json()["data"]["name"] == "Teh Pucuk Harum 350ml"

    # 3. PATCH (Partial Update)
    patch_payload = {"harga_jual": 4000.0, "stock": 30}
    res_patch = client.patch(
        f"/products/{prod_id}", headers=owner_headers, json=patch_payload
    )
    assert res_patch.status_code == 200
    updated_prod = res_patch.json()["data"]
    assert updated_prod["harga_jual"] == 4000.0
    assert updated_prod["stock"] == 30
    assert updated_prod["harga_modal"] == 2500.0  # modal tidak berubah

    # 4. DELETE (Soft Delete)
    res_delete = client.delete(f"/products/{prod_id}", headers=owner_headers)
    assert res_delete.status_code == 200
    assert "Berhasil menghapus data product" in res_delete.json()["message"]

    # 5. Verify Soft Delete: tidak ditemukan di endpoint get tunggal
    res_verify = client.get(f"/products/{prod_id}", headers=owner_headers)
    assert res_verify.status_code == 404


def test_product_search_and_pagination(client, owner_headers):
    """Pengujian query search dan metadata pagination produk."""
    # Pastikan ada produk untuk dites
    client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Kecap Bango Manis", "harga_modal": 8000, "harga_jual": 10000, "stock": 10},
    )

    # Search keyword
    res_search = client.get("/products/?search=Bango", headers=owner_headers)
    assert res_search.status_code == 200
    json_search = res_search.json()
    assert len(json_search["data"]) >= 1
    assert "Bango" in json_search["data"][0]["name"]

    # Pagination metadata check
    meta = json_search["meta"]
    assert "page" in meta
    assert "limit" in meta
    assert "total_data" in meta
    assert "total_page" in meta
