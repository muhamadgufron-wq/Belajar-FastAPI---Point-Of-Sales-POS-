def test_kasir_cannot_record_stock_in(client, kasir_headers):
    """KASIR dilarang mencatat kulakan/stok masuk (harus 403 Forbidden)."""
    payload = {
        "supplier": "Distributor Gelap",
        "items": [{"id_product": 1, "qty": 10, "harga_beli": 5000}],
    }
    response = client.post("/inventory/stock-in/", headers=kasir_headers, json=payload)
    assert response.status_code == 403


def test_stock_in_moving_average_calculation(client, owner_headers):
    """Memverifikasi penambahan stok dan rumus Moving Average dibulatkan ke Rupiah."""
    # 1. Buat produk: Stok 5 pcs @ Rp 10.000 (Nilai aset awal = 50.000)
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Kopi Sachet Premium", "harga_modal": 10000.0, "harga_jual": 15000.0, "stock": 5},
    )
    p_id = res_p.json()["id"]

    # 2. Kulakan: Masuk 10 pcs @ Rp 7.000 (Nilai belanja = 70.000)
    # Total nilai = 120.000, Total stok = 15 pcs
    # Modal rata-rata baru = 120.000 / 15 = Rp 8.000/pcs
    stock_in_payload = {
        "supplier": "PT Pangan Sejahtera",
        "note": "Faktur FAK-2026-99",
        "items": [{"id_product": p_id, "qty": 10, "harga_beli": 7000.0}],
    }
    res_stock_in = client.post("/inventory/stock-in/", headers=owner_headers, json=stock_in_payload)
    assert res_stock_in.status_code == 201
    stock_in_data = res_stock_in.json()["data"]
    stock_in_id = stock_in_data["id"]
    assert stock_in_data["total_biaya"] == 70000.0

    # 3. Cek kondisi produk setelah kulakan
    p_updated = client.get(f"/products/{p_id}", headers=owner_headers).json()["data"]
    assert p_updated["stock"] == 15
    assert p_updated["harga_modal"] == 8000.0

    # 4. Cek riwayat list & detail
    res_list = client.get("/inventory/stock-in/", headers=owner_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1

    res_detail = client.get(f"/inventory/stock-in/{stock_in_id}", headers=owner_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["data"]["supplier"] == "PT Pangan Sejahtera"


def test_stock_in_empty_stock_direct_cost(client, owner_headers):
    """Jika stok produk saat ini 0, harga modal langsung diset ke harga beli kulakan terbaru."""
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Mie Goreng Spesial", "harga_modal": 2500.0, "harga_jual": 3500.0, "stock": 0},
    )
    p_id = res_p.json()["id"]

    # Kulakan baru saat stok habis: 20 pcs @ Rp 2.800
    res_stock_in = client.post(
        "/inventory/stock-in/",
        headers=owner_headers,
        json={"supplier": "Agen Sembako", "items": [{"id_product": p_id, "qty": 20, "harga_beli": 2800.0}]},
    )
    assert res_stock_in.status_code == 201

    p_updated = client.get(f"/products/{p_id}", headers=owner_headers).json()["data"]
    assert p_updated["stock"] == 20
    assert p_updated["harga_modal"] == 2800.0
