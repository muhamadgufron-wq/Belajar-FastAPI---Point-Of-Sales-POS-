from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded


def get_real_ip(request: Request) -> str:
    """
    Mengambil IP address asli client.
    Mendukung header X-Forwarded-For (jika di belakang reverse proxy seperti Nginx / Cloudflare)
    dan fallback ke request.client.host atau 127.0.0.1.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Format X-Forwarded-For: "client_ip, proxy1_ip, proxy2_ip"
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


# Inisialisasi Limiter dengan default key function get_real_ip
limiter = Limiter(key_func=get_real_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom exception handler ketika limit request terlampaui (HTTP 429 Too Many Requests).
    Mengembalikan format response JSON standar dengan header Retry-After.
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Terlalu banyak percobaan request ({exc.detail}). Silakan tunggu beberapa saat.",
        },
        headers={"Retry-After": "60"},
    )
