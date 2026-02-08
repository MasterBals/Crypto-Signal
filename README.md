# EUR/JPY AI Dashboard (Decision Support)

Dieses Projekt stellt ein lokales Dashboard bereit, das sich ausschliesslich auf EUR/JPY fokussiert:
- Candlestick-Chart (TradingView Lightweight Charts)
- Technische Indikatoren (RSI, MACD, EMA20/EMA50, ATR)
- News via RSS + lokales Sentiment (VADER)
- Signal-Engine: BUY LIMIT, SELL LIMIT, NEUTRAL inkl. Entry, SL, TP, Confidence und Begruendung
- Auto-Refresh im Browser (standardmaessig alle 5 Minuten)
- Backend Cache + Hintergrund-Update (Scheduler) zur Stabilitaet
- Konfigurationsseite mit persistierten Einstellungen und Instrument-Auswahl (FX/Crypto)
- Lokale SQLite-Datenbank als Grundlage fuer Analyse und Backup

## Start (Docker)
```bash
docker compose up --build
```

Danach im Browser:

http://localhost:8887

Konfiguration:

http://localhost:8887/config

Hinweise
Kostenfrei: Keine API-Keys notwendig.

Datenquellen: yfinance (historische und aktuelle Kurse), RSS (News), optional TradingView TA (Sekundaerquelle fuer "Market Summary").

Waehrung: Standardmaessig werden EUR/JPY Kurse in USD umgerechnet (via USDJPY=X) und in USD angezeigt. Anpassung ueber die Konfiguration moeglich.

Instrumente: In der Konfiguration kann per Dropdown zwischen EUR/JPY und Kryptos (z.B. ETH/USD) gewechselt werden. Dieses Setting gilt fuer Chart, Analyse und News-Filter.

Backup: In der Konfigurationsseite kann ein ZIP-Backup der lokalen Datenbank und Einstellungen heruntergeladen werden.

Decision Support: Keine Broker-Anbindung, keine Order-Ausfuehrung.
