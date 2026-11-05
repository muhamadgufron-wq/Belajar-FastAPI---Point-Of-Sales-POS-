# Point of Sale (POS) Backend API

Backend RESTful API untuk sistem **Point of Sale (POS) / Kasir Toko** yang dirancang menggunakan arsitektur modular standar industri dengan **FastAPI**, **SQLModel**, dan database **PostgreSQL**.

---

## 🚀 Tech Stack

- **Language:** Python 3.14
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ORM:** [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic v2)
- **Database:** [PostgreSQL](https://www.postgresql.org/)
- **Security & Auth:** OAuth2 Password Bearer, Argon2id Password Hashing (`pwdlib`), dan PyJWT (JSON Web Token)
- **Package Manager:** [uv](https://docs.astral.sh/uv/) (Fast Python Package Manager)

---

## ✨ Fitur Utama

1. **🔐 Autentikasi, Otorisasi & Keamanan (RBAC & Rate Limiting):**
   - Registrasi user dengan password yang di-hash aman menggunakan algoritma **Argon2id**.
   - **Restricted Registration:** Endpoint pendaftaran akun baru (`POST /auth/register`) dikunci ketat khusus untuk role **`OWNER`**.
   - Login berbasis **OAuth2 Password Bearer** yang menghasilkan **JWT Access Token**.
   - **Anti Brute-Force Rate Limiting (SlowAPI):** Membatasi request login (`POST /auth/login`) maksimal 5 request per menit per IP dengan respon `429 Too Many Requests` dan header `Retry-After`. Mendukung reverse-proxy header (`X-Forwarded-For` / `X-Real-IP`).
   - **Hak Akses Berbasis Role (RBAC):**
     - **`KASIR`**: Berhak melayani transaksi kasir (`POST /transactions/`), melihat riwayat transaksi kasir, serta melihat katalog produk (`GET /products/`). Akses dibatasi agar tidak bisa mengubah katalog produk/kategori dan tidak bisa melihat laporan keuangan.
     - **`OWNER`**: Akses penuh ke seluruh sistem, termasuk penambahan/perubahan/penghapusan produk dan kategori, serta akses penuh ke laporan penjualan toko (omzet, laba bersih, dan produk terlaris).
   - Proteksi endpoint tingkat lanjut menggunakan FastAPI Dependency Injection (`get_current_user` & `require_roles`).
   - **Proteksi CORS (Cross-Origin Resource Sharing):** Whitelist domain frontend terpercaya (`localhost:5173`, `localhost:3000`, dll) untuk mencegah akses dari website pihak ketiga yang tidak berizin.

2. **📦 Manajemen Produk & Inventori (Katalog):**
   - CRUD lengkap untuk produk toko (nama, harga modal, harga jual, dan stok barang).
   - **Pencarian & Pagination:** Pencarian nama produk _case-insensitive_ (`search=...`) serta pembagian halaman data (`page=...&limit=...`) lengkap dengan metadata `total_data` dan `total_page`.
   - **Audit Timestamps:** Kolom `created_at` dan `updated_at` terisi dan terupdate otomatis dari database.
   - **Partial Update (`PATCH`):** Kasir/admin bisa mengedit sebagian data saja (misal hanya stok) tanpa harus mengirim ulang semua field.
   - **Soft Delete:** Menonaktifkan produk (`is_active = False`) agar riwayat transaksi dan struk masa lalu tidak rusak.

3. **🏷️ Manajemen Kategori & Relasi Database:**
   - Relasi _One-to-Many_ antara tabel `Category` dan `Product` menggunakan **Foreign Key**.
   - Fitur filter produk berdasarkan kategori (`GET /products/?id_category=1`).

4. **🛒 Engine Transaksi Kasir (Checkout & Void/Cancel):**
   - **Validasi Otomatis:** Memeriksa ketersediaan produk, memastikan stok mencukupi, dan memvalidasi kecukupan uang tunai pembeli.
   - **Pemotongan Stok Otomatis:** Mengurangi stok produk secara _real-time_ saat pembayaran berhasil.
   - **Atomic Database Transaction (ACID):** Jika terjadi kegagalan sistem di tengah jalan, seluruh perubahan transaksi di-rollback otomatis sehingga stok tidak berkurang sembarangan.
   - **Struk Belanja Digital:** Menghitung total transaksi, uang kembalian, dan menyimpan rincian barang belanjaan ke dalam tabel relasi `TransactionItem`.
   - **Format Cetak Struk Kasir Thermal (`GET /transactions/{id}/receipt` & `/receipt/print`):** Menghasilkan format struk belanja siap cetak ke printer thermal 58mm (tersedia dalam bentuk JSON DTO maupun raw `text/plain` untuk printer kasir Bluetooth/USB).
   - **Pembatalan / Refund Transaksi (`POST /transactions/{id}/cancel`):** Transaksi dapat dibatalkan khusus oleh `OWNER` dengan pencatatan alasan pembatalan. Stok produk otomatis dikembalikan dan transaksi yang batal otomatis dikeluarkan dari laporan penjualan/omzet toko.

5. **📊 Dashboard Laporan & Analitik Penjualan:**
   - Ringkasan otomatis performa toko (`GET /reports/summary`).
   - **Filter Periode / Rentang Tanggal:** Filter laporan berdasarkan tanggal (`?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`) berbasis zona waktu Indonesia (WIB) atau melihat data kumulatif (*all-time*) jika parameter dikosongkan.
   - Kalkulasi _real-time_ untuk total omzet, laba bersih (profit), total transaksi kasir, dan volume produk terjual.
   - Analisis produk terlaris (_Top 5 Best Seller_) beserta total omzet yang dihasilkan per item.

6. **📥 Modul Kulakan & Restock Stok Masuk (`/inventory/stock-in`):**
   - **Pencatatan Faktur Kulakan:** Mencatat barang masuk dari supplier dengan rincian nama supplier, catatan faktur/nota, kuantitas barang, dan harga beli modal.
   - **Kalkulasi Moving Average Otomatis:** Menghitung ulang harga modal produk secara adil menggunakan metode *Weighted Average Cost*, dibulatkan ke Rupiah utuh.
   - **Riwayat Pengeluaran Modal:** Audit trail lengkap untuk melacak seluruh histori kulakan barang masuk (`GET /inventory/stock-in` & `GET /inventory/stock-in/{id}`).
   - **Proteksi Role:** Khusus diakses oleh role `OWNER`.

7. **📐 Standard Response Envelope:**
   - Seluruh response API dibungkus rapi dalam format standar:
     ```json
     {
       "message": "Transaksi berhasil disimpan",
       "data": { ... }
     }
     ```

---

## 📂 Struktur Project (Layered Architecture)

```text
Belajar FastAPI/
├── app/
│   ├── core/                        # Konfigurasi Inti
│   │   ├── config.py                # Pydantic BaseSettings (.env reader)
│   │   ├── database.py              # Koneksi engine PostgreSQL & get_session
│   │   └── security.py              # Hash Argon2id & pembuat JWT
│   │
│   ├── models/                      # Definisi Tabel Database Fisik (SQLModel table=True)
│   │   ├── user.py                  # Tabel user kasir
│   │   ├── category.py              # Tabel kategori
│   │   ├── product.py               # Tabel produk
│   │   ├── transaction.py           # Tabel transaction & transactionitem
│   │   └── stock_in.py              # Tabel stock_in & stock_in_item (kulakan)
│   │
│   ├── schemas/                     # Validasi Request & Response DTO (Pydantic)
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── transaction.py
│   │   ├── report.py
│   │   └── stock_in.py
│   │
│   ├── routers/                     # Controller Endpoint REST API
│   │   ├── auth.py                  # Endpoint /auth (register, login, me)
│   │   ├── category.py              # Endpoint /categories
│   │   ├── product.py               # Endpoint /products
│   │   ├── transaction.py           # Endpoint /transactions (checkout kasir)
│   │   ├── report.py                # Endpoint /reports (laporan omzet & profit)
│   │   └── stock_in.py              # Endpoint /inventory/stock-in (kulakan stok)
│   │
│   ├── dependencies.py              # Satpam Auth & RBAC (get_current_user & require_roles)
│   └── main.py                      # FastAPI Orchestrator & Lifespan
│
├── .env.example                     # Template environment variables
├── pyproject.toml                   # Konfigurasi dependency & project metadata
└── README.md
```

---

## 🛠️ Cara Menjalankan Secara Lokal

### 1. Prasyarat

- Python 3.12+ (atau Python 3.14)
- Database PostgreSQL yang sedang berjalan
- Package manager `uv` terpasang

### 2. Setup Environment

Salin file `.env.example` menjadi `.env` dan sesuaikan kredensial PostgreSQL kamu:

```bash
cp .env.example .env
```

Isi file `.env`:

```env
DATABASE_URL=postgresql+psycopg://username:password@127.0.0.1:5432/nama_database
SECRET_KEY=buat_secret_key_acak_kamu_di_sini
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Jalankan Server

```bash
uv run fastapi dev app/main.py
```

### 5. Akses Dokumentasi Interaktif (Swagger UI)

Buka browser dan kunjungi:
👉 **`http://127.0.0.1:8000/docs`**

Gunakan tombol **Authorize 🔓** di Swagger UI untuk login sebagai kasir dan mulai mengeksekusi endpoint yang terproteksi.

### 6. Menjalankan Automated Test Suite (Pytest)

Jalankan seluruh skenario pengujian otomatis (Auth, RBAC, Produk, Transaksi, Restock, & Laporan) dengan satu perintah:

```bash
uv run pytest -v
```
