"""
core/config.py
==============
Reemplaza Django settings.py.
Usa pydantic-settings para validar fuertemente todas las variables de entorno
en el arranque. Si una variable crítica falta, la app falla rápido con un
mensaje claro (fail-fast) en lugar de lanzar errores en tiempo de ejecución.
"""

from functools import lru_cache
from typing import Literal
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import timedelta


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",           # Ignora variables extra en .env (ej. las de Django)
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "MangaAPI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ── Base de Datos MySQL ───────────────────────────────────────────────────
    DATABASE: str                         # Nombre de la BD (ex: DB_NAME en .env de Django)
    USER: str                             # Usuario BD
    PASSWORD_DB: str                      # Password BD
    HOST: str                             # Host BD
    PORT: int = 3306

    @property
    def database_url(self) -> str:
        """URL async para aiomysql + SQLAlchemy 2.0 (pure Python, sin compilador C++)."""
        return (
            f"mysql+aiomysql://{self.USER}:{self.PASSWORD_DB}"
            f"@{self.HOST}:{self.PORT}/{self.DATABASE}"
        )

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    JWT_ACCESS_MINUTES: int = 60
    JWT_REFRESH_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.JWT_ACCESS_MINUTES)

    @property
    def refresh_token_expire(self) -> timedelta:
        return timedelta(days=self.JWT_REFRESH_DAYS)

    # ── Backblaze B2 ──────────────────────────────────────────────────────────
    B2_ENDPOINT_URL: str = "https://s3.us-east-005.backblazeb2.com"
    B2_KEY_ID: str
    B2_APPLICATION_KEY: str
    B2_BUCKET_NAME: str = "MangaApi"

    # ── CDN / Workers ─────────────────────────────────────────────────────────
    CDN_COVER_BASE: str = "https://img.miswebtoons.uk"
    CDN_CHAPTER_BASE: str = "https://blackblaze.miswebtoons.uk"
    WORKER_URL: str = "http://127.0.0.1:8001"
    WORKER_API_KEY: str = ""

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "https://www.miswebtoons.uk",
        "https://mangareader-production.up.railway.app",
        "https://manga-reader-bv4.pages.dev",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ── Paginación ────────────────────────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 24
    MAX_PAGE_SIZE: int = 100

    # ── Sentry ────────────────────────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── Throttle ─────────────────────────────────────────────────────────────
    ANON_RATE_LIMIT: int = 100    # por minuto
    USER_RATE_LIMIT: int = 1000   # por minuto

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """En producción, ciertas variables son obligatorias."""
        if self.ENVIRONMENT == "production":
            if not self.SENTRY_DSN:
                raise ValueError("SENTRY_DSN es obligatorio en producción")
            if self.SECRET_KEY in ("", "changeme", "insecure"):
                raise ValueError("SECRET_KEY es insegura para producción")
        return self

    @field_validator("PORT", mode="before")
    @classmethod
    def parse_port(cls, v: str | int) -> int:
        return int(v)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Devuelve la instancia singleton de configuración.
    Usar como dependencia FastAPI: Depends(get_settings).
    """
    return Settings()


# Alias de conveniencia para importaciones directas
settings = get_settings()
