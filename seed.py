"""
Script shortcut untuk menjalankan Database Seeder Warung Umi Neneng.
Penggunaan:
    uv run python seed.py
    uv run python seed.py --username bos_neneng --password passwordKuat123
    uv run python seed.py --help
"""
from app.core.seed import main

if __name__ == "__main__":
    main()
