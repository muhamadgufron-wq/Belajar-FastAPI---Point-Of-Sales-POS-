from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Kredensial default untuk inisialisasi akun OWNER pertama (Database Seeder)
    FIRST_SUPERUSER_USERNAME: str = "owner_neneng"
    FIRST_SUPERUSER_PASSWORD: str = "OwnerNeneng123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
