from __future__ import annotations

from typing import Any

from app.state.trade_counter import TradeCounter


def _risk_reward(entry: float, stop_loss: float, take_profit: float, decision: str) -> float:
    if decision == "buy_limit":
        return (take_profit - entry) / (entry - stop_loss)
    if decision == "sell_limit":
        return (entry - take_profit) / (stop_loss - entry)
    return 0.0


def validate_decision(
    llm_output: dict[str, Any],
    market_state: dict[str, Any],
    config: dict[str, Any],
    trade_counter: TradeCounter,
) -> dict[str, Any]:
    decision = llm_output.get("decision", "no_trade")
    if decision == "no_trade":
        return llm_output

    counts = trade_counter.ensure_today()
    if counts.get("count", 0) >= config["risk"]["max_trades_per_day"]:
        return {"decision": "no_trade", "reasons": ["daily_trade_limit_reached"]}

    entry = float(llm_output.get("entry", 0))
    stop_loss = float(llm_output.get("stop_loss", 0))
    take_profit = float(llm_output.get("take_profit", 0))

    if stop_loss == 0 or take_profit == 0:
        return {"decision": "no_trade", "reasons": ["invalid_stop_or_target"]}

    rr = _risk_reward(entry, stop_loss, take_profit, decision)
    if rr < config["risk"]["min_rr"]:
        return {"decision": "no_trade", "reasons": ["invalid_rr"]}

    atr = float(market_state.get("atr", 0))
    sl_distance = abs(entry - stop_loss)
    if sl_distance < atr * config["risk"]["sl_atr_factor"]:
        return {"decision": "no_trade", "reasons": ["stop_too_tight"]}

    trade_counter.increment()
    return llm_output
