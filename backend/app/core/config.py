from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="iso15-draft")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    frontend_origin: str = Field(default="http://localhost:5173")

    database_url: str = Field(default="postgresql+psycopg://<user>:<password>@db:5432/iso15")

    valhalla_url: str = Field(default="http://valhalla:8002")
    valhalla_timeout_seconds: float = Field(default=10.0, ge=0.5, le=60.0)

    overpass_url: str = Field(default="https://overpass-api.de/api/interpreter")
    amenity_ingestion_radius_km: float = Field(default=10.0, gt=0.0, le=50.0)

    default_lat: float = Field(default=48.5216, ge=-90.0, le=90.0)
    default_lon: float = Field(default=9.0576, ge=-180.0, le=180.0)


settings = Settings()
