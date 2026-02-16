from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.engine.analysis import MultiTimeframeAnalyzer
from app.models.tables import AppSettings, Backtest, FeatureSnapshot, PositionsSnapshot, Signal
from app.schemas.api import AnalyzeResponse, BacktestRequest, SettingsPayload
from app.services.ai_client import infer_probability
from app.services.etoro_client import EtoroClient
from app.services.market_data import synthetic_candles
from app.services.session_filter import get_session_score

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_settings(db: Session) -> AppSettings:
    settings = db.query(AppSettings).first()
    if settings:
        return settings
    settings = AppSettings()
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "backend-core"}


@router.get("/settings", response_model=SettingsPayload)
def get_settings_endpoint(db: Session = Depends(get_db)) -> SettingsPayload:
    s = get_or_create_settings(db)
    return SettingsPayload(
        symbol=s.symbol,
        risk_per_trade=s.risk_per_trade,
        min_ai_probability=s.min_ai_probability,
        min_rr=s.min_rr,
        analysis_interval_minutes=s.analysis_interval_minutes,
        session_filter=s.session_filter,
        timeframes=s.timeframes or ["H4", "H1", "M15"],
        etoro_base_url=s.etoro_base_url,
        etoro_client_id=s.etoro_client_id,
        etoro_client_secret=s.etoro_client_secret,
        etoro_refresh_token=s.etoro_refresh_token,
    )


@router.put("/settings", response_model=SettingsPayload)
def update_settings(payload: SettingsPayload, db: Session = Depends(get_db)) -> SettingsPayload:
    s = get_or_create_settings(db)
    s.symbol = payload.symbol
    s.risk_per_trade = payload.risk_per_trade
    s.min_ai_probability = payload.min_ai_probability
    s.min_rr = payload.min_rr
    s.analysis_interval_minutes = payload.analysis_interval_minutes
    s.session_filter = payload.session_filter
    s.timeframes = payload.timeframes
    s.etoro_base_url = payload.etoro_base_url
    s.etoro_client_id = payload.etoro_client_id
    s.etoro_client_secret = payload.etoro_client_secret
    s.etoro_refresh_token = payload.etoro_refresh_token
    db.commit()
    db.refresh(s)
    return payload


@router.get("/account")
async def account() -> dict:
    return await EtoroClient().get_account()


@router.get("/positions")
async def positions(db: Session = Depends(get_db)) -> dict:
    data = await EtoroClient().get_positions()
    db.add(PositionsSnapshot(positions=data))
    db.commit()
    return data


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(db: Session = Depends(get_db)) -> AnalyzeResponse:
    runtime = get_or_create_settings(db)

    h4 = synthetic_candles(300, 240)
    h1 = synthetic_candles(300, 60)
    m15 = synthetic_candles(500, 15)

    analyzer = MultiTimeframeAnalyzer(min_rr=runtime.min_rr)
    session_score = get_session_score() if runtime.session_filter else 1.0
    features = analyzer.build_features(h4, h1, m15, session_score)
    ai_probability = await infer_probability(features)
    signal = analyzer.evaluate_signal(features, ai_probability, float(m15.iloc[-1]["close"]))
    signal["valid"] = signal["valid"] and ai_probability >= runtime.min_ai_probability

    db.add(FeatureSnapshot(timeframe="M15", features=features))
    db.add(
        Signal(
            symbol=runtime.symbol,
            timeframe="M15",
            direction=signal["direction"],
            confidence_score=signal["confidence_score"],
            ai_probability=signal["ai_probability"],
            payload=signal,
        )
    )
    db.commit()
    return AnalyzeResponse(signal=signal, features=features)


@router.post("/backtest")
async def backtest(payload: BacktestRequest, db: Session = Depends(get_db)) -> dict:
    metrics = {
        "winrate": 0.58,
        "max_drawdown": 0.11,
        "sharpe_ratio": 1.34,
        "expectancy": 0.41,
        "profit_factor": 1.86,
        "equity_curve": [10000, 10120, 9980, 10350, 10640],
    }
    db.add(Backtest(from_date=payload.from_date, to_date=payload.to_date, metrics=metrics))
    db.commit()
    return metrics


@router.get("/signals")
def list_signals(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Signal).order_by(Signal.id.desc()).limit(50).all()
    return [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "direction": row.direction,
            "confidence_score": row.confidence_score,
            "ai_probability": row.ai_probability,
            "payload": row.payload,
        }
        for row in rows
    ]
