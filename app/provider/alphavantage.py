from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests


@dataclass
class FatalConfigError(Exception):
    message: str


@dataclass
class RateLimitSkip:
    reason: str


def _write_state(payload: dict[str, Any], state_path: str = "/data/state/runtime_state.json") -> None:
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def fetch_market_data(config: dict[str, Any], logger) -> dict[str, Any] | None:
    api_key = config["alphavantage"]["api_key"]
    symbol = config["general"]["symbol"]
    interval = config["alphavantage"]["interval"]
    outputsize = config["alphavantage"]["outputsize"]

    params = {
        "function": "FX_INTRADAY",
        "from_symbol": symbol[:3],
        "to_symbol": symbol[3:],
        "interval": interval,
        "apikey": api_key,
        "outputsize": outputsize,
    }
    response = requests.get("https://www.alphavantage.co/query", params=params, timeout=30)

    if response.status_code == 401:
        logger.error("AlphaVantage returned 401: invalid API key.")
        _write_state(
            {
                "status": "fatal",
                "reason": "invalid_api_key",
                "action": "fix_config_and_restart",
            }
        )
        raise FatalConfigError("invalid_api_key")

    if response.status_code == 429 or "Thank you for using Alpha Vantage" in response.text:
        logger.warning("AlphaVantage rate limit hit. Skipping until next interval.")
        _write_state(
            {
                "last_fetch": datetime.utcnow().isoformat(timespec="minutes"),
                "skipped_reason": "rate_limit",
            }
        )
        raise RateLimitSkip("rate_limit")

    payload = response.json()
    if isinstance(payload, dict) and "Error Message" in payload:
        logger.error("AlphaVantage error response: %s", payload["Error Message"])
        _write_state(
            {
                "status": "fatal",
                "reason": "invalid_api_key",
                "action": "fix_config_and_restart",
            }
        )
        raise FatalConfigError("invalid_api_key")

    return payload
