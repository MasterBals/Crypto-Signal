from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeConfig(BaseModel):
    symbol: str = "EURJPY"
    risk_per_trade: float = 1.0
    min_ai_probability: float = 0.72
    min_rr: float = 2.2
    analysis_interval_minutes: int = 5
    session_filter: bool = True
    timeframes: list[str] = ["H4", "H1", "M15"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "eurjpy-institutional-analyst"
    analysis_mode_only: bool = Field(default=True, alias="ANALYSIS_MODE_ONLY")
    database_url: str = Field(default="postgresql+psycopg2://postgres:postgres@postgres:5432/eurjpy")
    redis_url: str = Field(default="redis://redis:6379/0")
    etoro_base_url: str = "https://api.etoro.example"
    etoro_client_id: str = "demo-client"
    etoro_client_secret: str = "demo-secret"
    etoro_refresh_token: str = "demo-refresh"
    ai_engine_url: str = "http://ai-engine:8001"

    def load_runtime_config(self) -> RuntimeConfig:
        path = Path("/app/config.json")
        if not path.exists():
            path = Path("config.json")
        return RuntimeConfig.model_validate_json(path.read_text(encoding="utf-8"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
