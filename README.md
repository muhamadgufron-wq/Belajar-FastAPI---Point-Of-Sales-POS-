# 🛒 Warung Umi Neneng - Point of Sale (POS) Backend API

Backend RESTful API untuk sistem **Point of Sale (POS) / Kasir Toko** yang dirancang menggunakan arsitektur modular standar industri dengan **FastAPI**, **SQLModel**, dan database **PostgreSQL**.

---

## 🚀 Tech Stack

* **Language:** Python 3.14
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **ORM:** [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic v2)
* **Database:** [PostgreSQL](https://www.postgresql.org/)
* **Security & Auth:** OAuth2 Password Bearer, Argon2id Password Hashing (`pwdlib`), dan PyJWT (JSON Web Token)
* **Package Manager:** [uv](https://docs.astral.sh/uv/) (Fast Python Package Manager)

---

## ✨ Fitur Utama

1. **🔐 Autentikasi & Otorisasi Kasir:**
   * Registrasi kasir baru dengan password yang di-hash aman menggunakan algoritma **Argon2id**.
   * Login berbasis **OAuth2 Password Bearer** yang menghasilkan **JWT Access Token**.
   * Proteksi endpoint menggunakan FastAPI Dependency Injection (`get_current_user`).

2. **📦 Manajemen Produk & Inventori (Katalog):**
   * CRUD lengkap untuk produk toko (nama, harga modal, harga jual, dan stok barang).
   * **Audit Timestamps:** Kolom `created_at` dan `updated_at` terisi dan terupdate otomatis dari database.
   * **Partial Update (`PATCH`):** Kasir/admin bisa mengedit sebagian data saja (misal hanya stok) tanpa harus mengirim ulang semua field.
   * **Soft Delete:** Menonaktifkan produk (`is_active = False`) agar riwayat transaksi dan struk masa lalu tidak rusak.

3. **🏷️ Manajemen Kategori & Relasi Database:**
   * Relasi *One-to-Many* antara tabel `Category` dan `Product` menggunakan **Foreign Key**.
   * Fitur filter produk berdasarkan kategori (`GET /products/?id_category=1`).

4. **🛒 Engine Transaksi Kasir (Checkout):**
   * **Validasi Otomatis:** Memeriksa ketersediaan produk, memastikan stok mencukupi, dan memvalidasi kecukupan uang tunai pembeli.
   * **Pemotongan Stok Otomatis:** Mengurangi stok produk secara *real-time* saat pembayaran berhasil.
   * **Atomic Database Transaction (ACID):** Jika terjadi kegagalan sistem di tengah jalan, seluruh perubahan transaksi di-rollback otomatis sehingga stok tidak berkurang sembarangan.
   * **Struk Belanja Digital:** Menghitung total transaksi, uang kembalian, dan menyimpan rincian barang belanjaan ke dalam tabel relasi `TransactionItem`.

5. **📐 Standard Response Envelope:**
   * Seluruh response API dibungkus rapi dalam format standar:
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
│   │   └── transaction.py           # Tabel transaction & transactionitem
│   │
│   ├── schemas/                     # Validasi Request & Response DTO (Pydantic)
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   └── transaction.py
│   │
│   ├── routers/                     # Controller Endpoint REST API
│   │   ├── auth.py                  # Endpoint /auth (register, login, me)
│   │   ├── category.py              # Endpoint /categories
│   │   ├── product.py               # Endpoint /products
│   │   └── transaction.py           # Endpoint /transactions (checkout kasir)
│   │
│   ├── dependencies.py              # Satpam Auth (get_current_user)
│   └── main.py                      # FastAPI Orchestrator & Lifespan
│
├── .env.example                     # Template environment variables
├── pyproject.toml                   # Konfigurasi dependency & project metadata
└── README.md
```

---

## 🛠️ Cara Menjalankan Secara Lokal

### 1. Prasyarat
* Python 3.12+ (atau Python 3.14)
* Database PostgreSQL yang sedang berjalan
* Package manager `uv` terpasang

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
