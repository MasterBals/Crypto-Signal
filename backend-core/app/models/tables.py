from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
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
