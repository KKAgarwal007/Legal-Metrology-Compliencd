"""Application configuration loaded from environment variables."""

import json
from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = None


class Settings(BaseSettings):
    """Central configuration for the Legal Metrology Compliance System."""

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=".env",
            case_sensitive=False,
            env_file_encoding="utf-8",
        )
    else:
        model_config = {"extra": "ignore"}

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/legal_metrology"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/legal_metrology"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = '["http://localhost:5173","http://localhost:3000"]'

    # Storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    # OCR
    ocr_engine: str = "paddleocr"
    ocr_lang: str = "en"
    ocr_confidence_high: float = 0.90
    ocr_confidence_medium: float = 0.60

    # LLM
    llm_provider: str = "gemini"
    gemini_api_key: str = "your-gemini-api-key-here"
    llm_model: str = "gemini-2.0-flash"

    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Security
    secret_key: str = "change-this-to-a-random-secret-key"
    access_token_expire_minutes: int = 60

    # App
    app_name: str = "Legal Metrology Compliance System"
    app_version: str = "1.0.0"
    debug: bool = True

    @property
    def cors_origins(self) -> List[str]:
        """Parse the JSON string of CORS origins into a list."""
        try:
            origins = json.loads(self.api_cors_origins)
            if isinstance(origins, list):
                return origins
            return [str(origins)]
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:5173", "http://localhost:3000"]

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
