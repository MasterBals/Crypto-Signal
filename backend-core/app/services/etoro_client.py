from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from app.core.config import get_settings

ALLOWED_ENDPOINTS = {
    "/account",
    "/portfolio",
    "/positions",
    "/market-data/candles",
    "/instruments",
}

BLOCKED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


class TradeExecutionBlockedError(RuntimeError):
    pass


class EtoroClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._token = ""
        self._expires_at = datetime.utcnow()

    async def _refresh_token(self) -> None:
        self._token = f"refreshed-{datetime.utcnow().timestamp()}"
        self._expires_at = datetime.utcnow() + timedelta(minutes=20)

    async def _request(self, method: str, endpoint: str, params: dict | None = None) -> dict:
        method = method.upper()
        if method in BLOCKED_METHODS:
            raise TradeExecutionBlockedError("Order/Trade methods are hard-blocked in ANALYSIS_MODE_ONLY")
        if endpoint not in ALLOWED_ENDPOINTS:
            raise PermissionError(f"Endpoint {endpoint} is not permitted")
        if datetime.utcnow() >= self._expires_at:
            await self._refresh_token()

        # Simulierter read-only API Zugriff. Kann durch echtes OAuth2-Flow ergänzt werden.
        async with httpx.AsyncClient(timeout=20) as client:
            _ = client
        return {"endpoint": endpoint, "params": params or {}, "token": self._token or "bootstrap-token"}

    async def get_account(self) -> dict:
        return await self._request("GET", "/account")

    async def get_portfolio(self) -> dict:
        return await self._request("GET", "/portfolio")

    async def get_positions(self) -> dict:
        return await self._request("GET", "/positions")

    async def get_instruments(self) -> dict:
        return await self._request("GET", "/instruments")

    async def get_candles(self, timeframe: str, limit: int = 400) -> dict:
        return await self._request("GET", "/market-data/candles", {"symbol": "EURJPY", "tf": timeframe, "limit": limit})

    async def place_order(self, *args, **kwargs) -> None:
        raise TradeExecutionBlockedError("Trading is forbidden. Analysis mode only.")
