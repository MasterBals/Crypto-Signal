# EUR/JPY AI Dashboard (Decision Support)

Dieses Projekt stellt ein lokales Dashboard bereit, das sich ausschliesslich auf EUR/JPY fokussiert:
- Candlestick-Chart (TradingView Lightweight Charts)
- Technische Indikatoren (RSI, MACD, EMA20/EMA50, ATR)
- News via RSS + lokales Sentiment (VADER)
- Signal-Engine: BUY LIMIT, SELL LIMIT, NEUTRAL inkl. Entry, SL, TP, Confidence und Begruendung
- Auto-Refresh im Browser (standardmaessig alle 5 Minuten)
- Backend Cache + Hintergrund-Update (Scheduler) zur Stabilitaet

## Start (Docker)
```bash
docker compose up --build
```

Danach im Browser:

http://localhost:8000

Hinweise
Kostenfrei: Keine API-Keys notwendig.

Datenquellen: yfinance (historische und aktuelle Kurse), RSS (News), optional TradingView TA (Sekundaerquelle fuer "Market Summary").

Decision Support: Keine Broker-Anbindung, keine Order-Ausfuehrung.
