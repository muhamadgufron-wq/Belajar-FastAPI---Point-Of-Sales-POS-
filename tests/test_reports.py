def test_kasir_cannot_access_reports(client, kasir_headers):
    """KASIR dilarang melihat laporan penjualan toko (harus 403 Forbidden)."""
    response = client.get("/reports/summary", headers=kasir_headers)
    assert response.status_code == 403


def test_report_summary_all_time(client, owner_headers):
    """OWNER dapat melihat ringkasan performa toko kumulatif (all-time)."""
    response = client.get("/reports/summary", headers=owner_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_omset" in data
    assert "total_profit" in data
    assert "total_transaksi" in data
    assert "total_produk_terjual" in data
    assert "top_produk" in data


def test_report_summary_date_filter(client, owner_headers):
    """OWNER dapat memfilter laporan penjualan berdasarkan rentang tanggal (WIB)."""
    response = client.get(
        "/reports/summary?start_date=2026-10-01&end_date=2026-11-30",
        headers=owner_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["start_date"] == "2026-10-01"
    assert data["end_date"] == "2026-11-30"


def test_report_invalid_date_range(client, owner_headers):
    """Validasi: menolak filter jika start_date lebih besar dari end_date (400)."""
    response = client.get(
        "/reports/summary?start_date=2026-11-30&end_date=2026-11-01",
        headers=owner_headers,
    )
    assert response.status_code == 400
    assert "tidak boleh lewat dari tanggal akhir" in response.json()["detail"]


def test_report_excludes_cancelled_transactions(client, owner_headers, kasir_headers):
    """Memastikan transaksi yang berstatus CANCELLED tidak masuk ke perhitungan omzet & profit."""
    # 1. Catat omset sebelum transaksi baru
    omset_awal = client.get("/reports/summary", headers=owner_headers).json()["data"]["total_omset"]

    # 2. Buat produk dan checkout
    res_p = client.post(
        "/products/",
        headers=owner_headers,
        json={"name": "Susu Kental Manis", "harga_modal": 8000, "harga_jual": 12000, "stock": 5},
    )
    p_id = res_p.json()["id"]

    res_trx = client.post(
        "/transactions/",
        headers=kasir_headers,
        json={"uang_bayar": 50000, "items": [{"id_product": p_id, "quantity": 1}]},
    )
    trx_id = res_trx.json()["data"]["id"]

    # Omset harus bertambah Rp 12.000
    omset_setelah_beli = client.get("/reports/summary", headers=owner_headers).json()["data"]["total_omset"]
    assert omset_setelah_beli == omset_awal + 12000.0

    # 3. Batalkan transaksi
    client.post(
        f"/transactions/{trx_id}/cancel",
        headers=owner_headers,
        json={"reason": "Uji Coba Laporan"},
    )

    # 4. Omset harus kembali ke omset awal (transaksi yang batal otomatis dikeluarkan)
    omset_setelah_cancel = client.get("/reports/summary", headers=owner_headers).json()["data"]["total_omset"]
    assert omset_setelah_cancel == omset_awal
