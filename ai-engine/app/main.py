from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.linear_model import LogisticRegression

MODEL_PATH = Path("/app/model_eurjpy.pkl")
FEATURE_COLUMNS = [
    "ema_distance_ratio",
    "rsi_slope",
    "atr_expansion_ratio",
    "distance_to_vwap",
    "session_score",
    "volatility_spike_score",
    "structure_strength_index",
    "liquidity_grab_score",
    "h4_trend_bull",
    "h1_trend_bull",
    "m15_bos_bull",
    "atr14",
]

logger = logging.getLogger("ai-engine")
logging.basicConfig(level=logging.INFO)


class InferPayload(BaseModel):
    features: dict


app = FastAPI(title="eurjpy-institutional-analyst ai-engine")


def _build_training_frame(size: int = 2500) -> tuple[pd.DataFrame, pd.Series]:
    np.random.seed(42)
    frame = pd.DataFrame(
        {
            "ema_distance_ratio": np.random.normal(0, 0.02, size),
            "rsi_slope": np.random.normal(0, 1, size),
            "atr_expansion_ratio": np.random.uniform(0.8, 2.2, size),
            "distance_to_vwap": np.random.normal(0, 0.01, size),
            "session_score": np.random.choice([0.2, 1.0], size=size, p=[0.45, 0.55]),
            "volatility_spike_score": np.random.uniform(0, 1, size),
            "structure_strength_index": np.random.uniform(0, 1, size),
            "liquidity_grab_score": np.random.choice([0.0, 1.0], size=size),
            "h4_trend_bull": np.random.choice([0, 1], size=size),
            "h1_trend_bull": np.random.choice([0, 1], size=size),
            "m15_bos_bull": np.random.choice([0, 1], size=size),
            "atr14": np.random.uniform(0.02, 0.8, size),
        }
    )
    target = (
        (frame["atr_expansion_ratio"] > 1.1)
        & (frame["structure_strength_index"] > 0.45)
        & (frame["session_score"] > 0.3)
    ).astype(int)

    # Schutz gegen Ein-Klassen-Datensatz
    if target.nunique() == 1:
        target.iloc[0] = 1 - target.iloc[0]

    return frame, target


def _train_model() -> object:
    frame, target = _build_training_frame()
    try:
        from lightgbm import LGBMClassifier

        model = LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=31, random_state=42)
        model.fit(frame[FEATURE_COLUMNS], target)
        logger.info("Trained LightGBM model")
        return model
    except Exception as exc:  # pragma: no cover - runtime fallback in container
        logger.warning("LightGBM unavailable, fallback to LogisticRegression: %s", exc)
        model = LogisticRegression(max_iter=1000)
        model.fit(frame[FEATURE_COLUMNS], target)
        return model


def ensure_model() -> None:
    if MODEL_PATH.exists():
        return
    model = _train_model()
    joblib.dump(model, MODEL_PATH)
    logger.info("Saved model to %s", MODEL_PATH)


@app.on_event("startup")
def startup() -> None:
    ensure_model()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-engine", "model_exists": MODEL_PATH.exists()}


@app.post("/infer")
def infer(payload: InferPayload) -> dict:
    ensure_model()
    model = joblib.load(MODEL_PATH)
    row = [payload.features.get(col, 0.0) for col in FEATURE_COLUMNS]
    probability = float(model.predict_proba([row])[0][1])
    return {"probability": probability, "show_signal": probability > 0.72}
