from __future__ import annotations

import os
import sqlite3
from typing import Iterable

import pandas as pd

DB_PATH = os.getenv("DB_PATH", "/app/data/market.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT NOT NULL,
            ts INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL,
            PRIMARY KEY (symbol, ts)
        );
        """
    )
    conn.commit()
    conn.close()


def upsert_candles(symbol: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    conn = get_connection()
    rows: Iterable[tuple] = [
        (
            symbol,
            int(pd.Timestamp(idx).timestamp()),
            float(row["Open"]),
            float(row["High"]),
            float(row["Low"]),
            float(row["Close"]),
            float(row.get("Volume", 0) or 0),
        )
        for idx, row in df.iterrows()
    ]
    conn.executemany(
        """
        INSERT INTO candles (symbol, ts, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, ts) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            volume=excluded.volume;
        """,
        rows,
    )
    conn.commit()
    conn.close()


def load_candles(symbol: str, since_ts: int) -> pd.DataFrame:
    conn = get_connection()
    query = "SELECT ts, open, high, low, close, volume FROM candles WHERE symbol = ? AND ts >= ? ORDER BY ts"
    df = pd.read_sql_query(query, conn, params=(symbol, since_ts))
    conn.close()
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df = df.set_index("ts")
    return df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
