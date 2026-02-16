from pydantic import BaseModel


class BacktestRequest(BaseModel):
    from_date: str
    to_date: str


class AnalyzeResponse(BaseModel):
    signal: dict
    features: dict
