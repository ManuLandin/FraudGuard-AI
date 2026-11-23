from pathlib import Path
from urllib.parse import urlsplit

from pydantic import AnyHttpUrl, TypeAdapter, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///" + (BACKEND_DIR / "fraudguard.db").as_posix()
    model_path: Path = BACKEND_DIR / "artifacts" / "isolation_forest.joblib"
    max_upload_bytes: int = Field(default=5 * 1024 * 1024, ge=1, le=20 * 1024 * 1024)
    max_csv_rows: int = Field(default=10000, ge=1, le=100000)

    @field_validator("database_url")
    @classmethod
    def validate_database(cls, value: str) -> str:
        if not value.startswith("sqlite:///"):
            raise ValueError("Se requiere una URL SQLite local.")
        return value

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            TypeAdapter(AnyHttpUrl).validate_python(origin)
            parts = urlsplit(origin)
            if (
                parts.path
                or parts.query
                or parts.fragment
                or parts.username is not None
                or parts.password is not None
                or "*" in origin
                or origin != origin.strip()
            ):
                raise ValueError("Cada origen CORS debe incluir solo esquema, host y puerto opcional.")
        return origins
