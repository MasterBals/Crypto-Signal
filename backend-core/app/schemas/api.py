from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    from_date: str
    to_date: str


class AnalyzeResponse(BaseModel):
    signal: dict
    features: dict


class SettingsPayload(BaseModel):
    symbol: str = "EURJPY"
    risk_per_trade: float = 1.0
    min_ai_probability: float = 0.72
    min_rr: float = 2.2
    analysis_interval_minutes: int = 5
    session_filter: bool = True
    timeframes: list[str] = Field(default_factory=lambda: ["H4", "H1", "M15"])
    etoro_base_url: str = "https://api.etoro.example"
    etoro_client_id: str = ""
    etoro_client_secret: str = ""
    etoro_refresh_token: str = ""
