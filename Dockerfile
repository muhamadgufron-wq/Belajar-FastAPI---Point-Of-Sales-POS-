# ==========================================
# 🐳 DOCKERFILE - WARUNG UMI NENENG POS API
# ==========================================

# 1. Base Image: Linux Debian Bookworm Slim dengan Python 3.12 resmi (Ringan, aman & stabil)
FROM python:3.12-slim-bookworm

# Install libpq runtime library untuk koneksi database PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*

# 2. Ambil binary 'uv' resmi dari Astral (Image multi-stage copy)
# Ini membuat instalasi dependensi super cepat (jauh lebih cepat dari pip biasa)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Tentukan direktori kerja utama di dalam container
WORKDIR /app

# 4. Atur environment variables untuk optimasi Python & uv
ENV UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

# 5. Layer Caching: Salin file dependensi terlebih dahulu
# Jika source code aplikasi kita diedit, Docker TIDAK perlu mendownload ulang package!
COPY pyproject.toml uv.lock ./

# 6. Install seluruh dependensi production ke virtual environment
RUN uv sync --frozen --no-install-project --no-dev

# 7. Salin seluruh source code aplikasi ke dalam container
COPY . .

# 8. Daftarkan virtualenv ke PATH agar perintah uvicorn/fastapi bisa langsung dieksekusi
ENV PATH="/app/.venv/bin:$PATH"

# 9. Buka port 8000 untuk diakses dari luar
EXPOSE 8000

# 10. Perintah utama saat container dinyalakan
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
