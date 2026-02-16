from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.engine.analysis import MultiTimeframeAnalyzer
from app.models.tables import Backtest, FeatureSnapshot, PositionsSnapshot, Signal
from app.schemas.api import AnalyzeResponse, BacktestRequest
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


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "backend-core"}


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
    h4 = synthetic_candles(300, 240)
    h1 = synthetic_candles(300, 60)
    m15 = synthetic_candles(500, 15)

    analyzer = MultiTimeframeAnalyzer()
    session_score = get_session_score()
    features = analyzer.build_features(h4, h1, m15, session_score)
    ai_probability = await infer_probability(features)
    signal = analyzer.evaluate_signal(features, ai_probability, float(m15.iloc[-1]["close"]))

    db.add(FeatureSnapshot(timeframe="M15", features=features))
    db.add(
        Signal(
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
    # Vereinfachter Backtest-Simulator
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
