def test_checkout_empty_cart(client, kasir_headers):
    """Menolak checkout jika keranjang belanja kasir kosong (400)."""
    response = client.post(
        "/transactions/",
        headers=kasir_headers,
        json={"uang_bayar": 50000.0, "items": []},
    )
    assert response.status_code == 400
    assert "Keranjang belanja tidak boleh kosong" in response.json()["detail"]


def test_checkout_insufficient_payment(client, owner_headers, kasir_headers):
    """Menolak checkout jika uang yang diserahkan pembeli kurang (400)."""
    # 1. Buat produk untuk dites
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Susu UHT Cokelat", "harga_modal": 4000, "harga_jual": 6000, "stock": 10},
    )
    p_id = res_p.json()["id"]

    # 2. Checkout 2 pcs = Rp 12.000, tapi bayar Rp 10.000
    response = client.post(
        "/transactions/",
        headers=kasir_headers,
        json={"uang_bayar": 10000.0, "items": [{"id_product": p_id, "quantity": 2}]},
    )
    assert response.status_code == 400
    assert "Uang bayar kurang" in response.json()["detail"]


def test_checkout_insufficient_stock(client, owner_headers, kasir_headers):
    """Menolak checkout jika jumlah yang dibeli melebihi stok yang ada di toko (400)."""
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Roti Tawar Gandum", "harga_modal": 12000, "harga_jual": 15000, "stock": 3},
    )
    p_id = res_p.json()["id"]

    # Beli 5 pcs padahal stok cuma 3 pcs
    response = client.post(
        "/transactions/",
        headers=kasir_headers,
        json={"uang_bayar": 100000.0, "items": [{"id_product": p_id, "quantity": 5}]},
    )
    assert response.status_code == 400
    assert "tidak mencukupi" in response.json()["detail"]


def test_checkout_success_and_cancellation_lifecycle(client, owner_headers, kasir_headers):
    """Siklus lengkap: Checkout kasir, potong stok, penolakan kasir saat cancel, dan owner cancel yang memulihkan stok."""
    # 1. Siapkan produk: Stok 10
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Air Mineral 600ml", "harga_modal": 2000, "harga_jual": 3000, "stock": 10},
    )
    p_id = res_p.json()["id"]

    # 2. Kasir Checkout 4 pcs (Total = Rp 12.000, Bayar = Rp 20.000, Kembalian = Rp 8.000)
    res_checkout = client.post(
        "/transactions/",
        headers=kasir_headers,
        json={"uang_bayar": 20000.0, "items": [{"id_product": p_id, "quantity": 4}]},
    )
    assert res_checkout.status_code == 201
    trx_data = res_checkout.json()["data"]
    trx_id = trx_data["id"]
    assert trx_data["total_transaksi"] == 12000.0
    assert trx_data["uang_kembali"] == 8000.0
    assert trx_data["status"] == "COMPLETED"

    # 3. Verifikasi stok berkurang: 10 - 4 = 6 pcs
    p_after = client.get(f"/products/{p_id}", headers=owner_headers).json()["data"]
    assert p_after["stock"] == 6

    # 4. KASIR mencoba membatalkan transaksi (harus 403 Forbidden)
    res_k_cancel = client.post(f"/transactions/{trx_id}/cancel", headers=kasir_headers)
    assert res_k_cancel.status_code == 403

    # 5. OWNER membatalkan transaksi dengan alasan (harus 200 OK)
    res_o_cancel = client.post(
        f"/transactions/{trx_id}/cancel",
        headers=owner_headers,
        json={"reason": "Pembeli membatalkan pesanan"},
    )
    assert res_o_cancel.status_code == 200
    cancelled_data = res_o_cancel.json()["data"]
    assert cancelled_data["status"] == "CANCELLED"
    assert cancelled_data["alasan_pembatalan"] == "Pembeli membatalkan pesanan"
    assert cancelled_data["cancelled_at"] is not None

    # 6. Verifikasi stok otomatis dipulihkan kembali: 6 + 4 = 10 pcs
    p_restored = client.get(f"/products/{p_id}", headers=owner_headers).json()["data"]
    assert p_restored["stock"] == 10

    # 7. Membatalkan transaksi yang sudah berstatus CANCELLED ditolak (400 Bad Request)
    res_again = client.post(f"/transactions/{trx_id}/cancel", headers=owner_headers)
    assert res_again.status_code == 400
    assert "sudah dibatalkan sebelumnya" in res_again.json()["detail"]


def test_transaction_receipt_format_and_print(client, owner_headers, kasir_headers):
    """Menguji pembuatan format struk kasir profesional (JSON dan Raw Plain Text)."""
    # 1. Buat produk & checkout oleh KASIR
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Kacang Sukro Oven", "harga_modal": 1500, "harga_jual": 2000, "stock": 20},
    )
    p_id = res_p.json()["id"]

    res_checkout = client.post(
        "/transactions/",
        headers=kasir_headers,
        json={"uang_bayar": 10000.0, "items": [{"id_product": p_id, "quantity": 3}]},
    )
    trx_id = res_checkout.json()["data"]["id"]

    # 2. Kasir mengambil format struk via JSON
    res_receipt = client.get(f"/transactions/{trx_id}/receipt", headers=kasir_headers)
    assert res_receipt.status_code == 200
    receipt_data = res_receipt.json()["data"]
    assert receipt_data["store_name"] == "Warung Umi Neneng"
    assert receipt_data["kasir"] == "kasir_pos2"
    assert "WARUNG UMI NENENG" in receipt_data["receipt_text"]
    assert "Kacang Sukro Oven" in receipt_data["receipt_text"]
    assert "Total Belanja" in receipt_data["receipt_text"]

    # 3. Kasir mencetak format teks murni (Raw text/plain)
    res_print = client.get(f"/transactions/{trx_id}/receipt/print", headers=kasir_headers)
    assert res_print.status_code == 200
    assert "text/plain" in res_print.headers["content-type"]
    assert "WARUNG UMI NENENG" in res_print.text
    assert "Kembalian" in res_print.text
