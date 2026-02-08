from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from app.decision.validator import validate_decision
from app.features.indicators import compute_indicators
from app.features.market_structure import analyze_market_structure
from app.features.resample import resample_market_data
from app.llm.ollama_client import call_ollama
from app.llm.prompts import build_prompt
from app.output.writer import SignalWriter
from app.provider.alphavantage import fetch_market_data
from app.scheduler import Scheduler
from app.state.trade_counter import TradeCounter
from app.utils.logging import setup_logger
from app.utils.time import now_in_tz


def load_config(path: str = "/config/config.yaml") -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_llm_input(config: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": config["general"]["symbol"],
        "interval": config["alphavantage"]["interval"],
        "market_state": {
            "trend": features["trend"],
            "rsi": features["rsi"],
            "atr": features["atr"],
        },
        "levels": {
            "support": features["support"],
            "resistance": features["resistance"],
        },
        "risk": {
            "min_rr": config["risk"]["min_rr"],
            "sl_atr_factor": config["risk"]["sl_atr_factor"],
            "max_trades_per_day": config["risk"]["max_trades_per_day"],
        },
    }


def main() -> None:
    config = load_config()
    logger = setup_logger()
    trade_counter = TradeCounter(timezone=config["general"]["timezone"])
    writer = SignalWriter()

    def on_tick() -> None:
        market_data = fetch_market_data(config, logger)
        if market_data is None:
            return

        resampled = resample_market_data(market_data, config["alphavantage"]["interval"])
        indicators = compute_indicators(resampled, config)
        structure = analyze_market_structure(resampled)
        features = {**indicators, **structure}

        llm_input = build_llm_input(config, features)
        prompt = build_prompt(llm_input)
        llm_output = call_ollama(config["llm"]["model"], config["llm"]["temperature"], prompt)

        final_decision = validate_decision(llm_output, llm_input["market_state"], config, trade_counter)

        payload = {
            "raw_hash": hash_payload(market_data),
            "feature_snapshot": features,
            "llm_input": llm_input,
            "llm_output": llm_output,
            "final_decision": final_decision,
        }

        now = now_in_tz(config["general"]["timezone"])
        writer.write(payload, config["general"]["symbol"], config["alphavantage"]["interval"], now)

    scheduler = Scheduler(config=config, logger=logger, on_tick=on_tick)
    scheduler.run()


if __name__ == "__main__":
    main()
