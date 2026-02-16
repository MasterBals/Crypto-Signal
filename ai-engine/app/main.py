from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI
from lightgbm import LGBMClassifier
from pydantic import BaseModel

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


class InferPayload(BaseModel):
    features: dict


app = FastAPI(title="eurjpy-institutional-analyst ai-engine")


def train_and_save() -> None:
    np.random.seed(42)
    size = 2500
    frame = pd.DataFrame({
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
    })
    y = (
        (frame["atr_expansion_ratio"] > 1.1)
        & (frame["structure_strength_index"] > 0.45)
        & (frame["session_score"] > 0.3)
    ).astype(int)

    model = LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=31, random_state=42)
    model.fit(frame[FEATURE_COLUMNS], y)
    joblib.dump(model, MODEL_PATH)


@app.on_event("startup")
def startup() -> None:
    if not MODEL_PATH.exists():
        train_and_save()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-engine"}


@app.post("/infer")
def infer(payload: InferPayload) -> dict:
    model = joblib.load(MODEL_PATH)
    row = [payload.features.get(col, 0.0) for col in FEATURE_COLUMNS]
    prob = float(model.predict_proba([row])[0][1])
    return {"probability": prob, "show_signal": prob > 0.72}
