from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    symbol: Mapped[str] = mapped_column(String(32), default="EURJPY")
    timeframe: Mapped[str] = mapped_column(String(8))
    direction: Mapped[str] = mapped_column(String(8))
    confidence_score: Mapped[float] = mapped_column(Float)
    ai_probability: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)


class FeatureSnapshot(Base):
    __tablename__ = "features_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    symbol: Mapped[str] = mapped_column(String(32), default="EURJPY")
    timeframe: Mapped[str] = mapped_column(String(8))
    features: Mapped[dict] = mapped_column(JSON)


class Backtest(Base):
    __tablename__ = "backtests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    from_date: Mapped[str] = mapped_column(String(32))
    to_date: Mapped[str] = mapped_column(String(32))
    metrics: Mapped[dict] = mapped_column(JSON)


class PositionsSnapshot(Base):
    __tablename__ = "positions_snapshot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    positions: Mapped[dict] = mapped_column(JSON)


class MarketRegime(Base):
    __tablename__ = "market_regime"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    symbol: Mapped[str] = mapped_column(String(32), default="EURJPY")
    regime: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSON)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    symbol: Mapped[str] = mapped_column(String(32), default="EURJPY")
    risk_per_trade: Mapped[float] = mapped_column(Float, default=1.0)
    min_ai_probability: Mapped[float] = mapped_column(Float, default=0.72)
    min_rr: Mapped[float] = mapped_column(Float, default=2.2)
    analysis_interval_minutes: Mapped[int] = mapped_column(Integer, default=5)
    session_filter: Mapped[bool] = mapped_column(Boolean, default=True)
    timeframes: Mapped[dict] = mapped_column(JSON, default=["H4", "H1", "M15"])

    etoro_base_url: Mapped[str] = mapped_column(String(255), default="https://api.etoro.example")
    etoro_client_id: Mapped[str] = mapped_column(String(255), default="")
    etoro_client_secret: Mapped[str] = mapped_column(Text, default="")
    etoro_refresh_token: Mapped[str] = mapped_column(Text, default="")
