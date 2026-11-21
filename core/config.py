"""Configuración de la aplicación usando pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno del backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    supabase_url: str
    cors_origins: str = ""
    dni_api_url: str = "https://dniruc.apisperu.com/api/v1/dni"
    dni_api_token: str = ""
    safe_browsing_api_key: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte CORS_ORIGINS (separado por comas) en una lista."""
        return [
            origen.strip().rstrip("/")
            for origen in self.cors_origins.split(",")
            if origen.strip()
        ]

    @property
    def supabase_issuer(self) -> str:
        """Issuer esperado en los JWT de Supabase."""
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        """URL del JWKS de Supabase para validar la firma ES256."""
        return f"{self.supabase_issuer}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración una sola vez por proceso."""
    return Settings()
