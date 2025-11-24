from __future__ import annotations

import json
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import settings as app_settings

# Load .env early to make sure KG_* variables are available
load_dotenv()


class DatabaseSettings(BaseModel):
    url: str = Field(
        default=app_settings.DATABASE_URL,
        description="PostgreSQL connection string used for KG sessions/cache storage",
    )


class Neo4jSettings(BaseModel):
    url: str = Field("neo4j://localhost:7687", description="Neo4j bolt URL")
    username: str = Field("neo4j", description="Neo4j user")
    password: str = Field("password", description="Neo4j password")


class GeminiSettings(BaseModel):
    api_keys_raw: str | List[str] | None = Field(None, alias="api_keys")
    chat_model: str = Field("models/gemini-2.5-flash", description="Gemini chat model id")

    @property
    def api_keys(self) -> List[str]:
        raw = self.api_keys_raw
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(k).strip() for k in raw if str(k).strip()]
        if isinstance(raw, str):
            text = raw.strip()
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return [str(k).strip() for k in parsed if str(k).strip()]
                except Exception:
                    pass
            return [k.strip() for k in text.split(",") if k.strip()]
        return []


class EmbeddingSettings(BaseModel):
    text_model: str = Field("keepitreal/vietnamese-sbert")
    image_model: str = Field("openai/clip-vit-base-patch32")
    text_batch_size: int = 32
    image_batch_size: int = 16
    text_max_length: int = 10_000
    image_max_size: tuple[int, int] = (1024, 1024)


class CacheSettings(BaseModel):
    ttl_hours: int = 24
    session_ttl_hours: int = 168


class LanguageSettings(BaseModel):
    data_language: str = "vi"
    supported_languages: List[str] = Field(default_factory=lambda: ["vi", "en"])
    auto_translate: bool = True


class KGSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KG_", env_nested_delimiter="__")

    database: DatabaseSettings = DatabaseSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    gemini: GeminiSettings = GeminiSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    cache: CacheSettings = CacheSettings()
    language: LanguageSettings = LanguageSettings()
    log_level: str = "INFO"


settings = KGSettings()
