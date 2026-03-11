"""GroundedAI Backend Configuration.

All configuration is loaded from environment variables with sensible defaults.
Uses Pydantic BaseSettings for validation and type coercion.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    app_env: str = Field(default="development", alias="APP_ENV")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Supabase ---
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")

    # --- Ollama ---
    ollama_base_url: str = Field(
        default="http://ollama:11434", alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(
        default="mistral:7b-instruct-q4_K_M", alias="OLLAMA_MODEL"
    )

    # --- FAISS ---
    faiss_index_path: str = Field(
        default="./data/faiss_index", alias="FAISS_INDEX_PATH"
    )

    # --- Redis ---
    redis_url: str = Field(default="redis://redis:6379", alias="REDIS_URL")
    redis_memory_window: int = Field(default=3, alias="REDIS_MEMORY_WINDOW")

    # --- Upload ---
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")

    # --- Retrieval ---
    top_k_default: int = Field(default=5, alias="TOP_K_DEFAULT")
    chunk_size_tokens: int = Field(default=750, alias="CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int = Field(default=100, alias="CHUNK_OVERLAP_TOKENS")
    confidence_threshold: float = Field(
        default=0.35, alias="CONFIDENCE_THRESHOLD"
    )
    hybrid_alpha: float = Field(default=0.7, alias="HYBRID_ALPHA")

    # --- CORS ---
    cors_origins: str = Field(
        default="http://localhost:3000", alias="CORS_ORIGINS"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
