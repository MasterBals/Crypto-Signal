# Trading AI

## Projektstruktur (Root-Level)
```
trading-ai/
│
├─ docker-compose.yml
│
├─ config/
│  └─ config.yaml
│
├─ app/
│  ├─ main.py
│  ├─ scheduler.py
│  ├─ provider/
│  │  ├─ __init__.py
│  │  └─ alphavantage.py
│  │
│  ├─ features/
│  │  ├─ __init__.py
│  │  ├─ indicators.py
│  │  ├─ market_structure.py
│  │  └─ resample.py
│  │
│  ├─ llm/
│  │  ├─ __init__.py
│  │  ├─ ollama_client.py
│  │  └─ prompts.py
│  │
│  ├─ decision/
│  │  ├─ __init__.py
│  │  ├─ rules.py
│  │  └─ validator.py
│  │
│  ├─ state/
│  │  ├─ __init__.py
│  │  ├─ trade_counter.py
│  │  └─ runtime_state.py
│  │
│  ├─ output/
│  │  ├─ __init__.py
│  │  ├─ writer.py
│  │  └─ deduplicator.py
│  │
│  ├─ schema/
│  │  ├─ market_input.schema.json
│  │  ├─ llm_output.schema.json
│  │  └─ signal_record.schema.json
│  │
│  └─ utils/
│     ├─ time.py
│     ├─ logging.py
│     └─ retry.py
│
├─ data/
│  ├─ raw/
│  ├─ candles/
│  ├─ signals/
│  └─ state/
│
└─ ollama/
   └─ models/
```

## Services und Verantwortlichkeiten
- **app**: Führt den Scheduler aus, ruft AlphaVantage ab, berechnet Features, baut LLM-Input, ruft Ollama, validiert Entscheidungen und schreibt Signale.
- **ollama**: LLM-Runtime für das Modell (z. B. `llama3:8b`).

## Konfigurationsdateien (vollständig)
### `docker-compose.yml`
```yaml
version: "3.9"

services:
  app:
    image: python:3.11-slim
    container_name: trading-ai-app
    volumes:
      - ./app:/app
      - ./config:/config
      - ./data:/data
    working_dir: /app
    command: ["python", "main.py"]
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama
    container_name: trading-ai-ollama
    volumes:
      - ./ollama:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped
```

### `config/config.yaml`
```yaml
general:
  timezone: "Europe/Zurich"
  symbol: "EURJPY"

alphavantage:
  api_key: "REQUIRED"
  interval: "15min"
  outputsize: "compact"

usage_schedule:
  weekdays: ["MO", "TU", "WE", "TH", "FR"]
  windows:
    - start: "06:30"
      end: "22:00"

fetch_policy:
  auto_from_usage: true
  jitter_seconds: 30
  backfill_on_start: true

analysis:
  min_history_bars: 200
  ema_periods: [20, 50, 200]
  rsi_period: 14
  atr_period: 14

risk:
  min_rr: 1.8
  sl_atr_factor: 1.3
  sl_min_pips: 12
  max_trades_per_day: 2

llm:
  model: "llama3:8b"
  temperature: 0.25
```

## JSON-Schemas (verbindlich)
### Markt-Input (`market_input.schema.json`)
```json
{
  "type": "object",
  "required": ["symbol", "interval", "market_state", "levels", "risk"],
  "properties": {
    "symbol": { "type": "string" },
    "interval": { "type": "string" },
    "market_state": {
      "type": "object",
      "required": ["trend", "rsi", "atr"],
      "properties": {
        "trend": { "type": "string" },
        "rsi": { "type": "number" },
        "atr": { "type": "number" }
      }
    },
    "levels": {
      "type": "object",
      "properties": {
        "support": { "type": "array", "items": { "type": "number" } },
        "resistance": { "type": "array", "items": { "type": "number" } }
      }
    },
    "risk": {
      "type": "object",
      "required": ["min_rr", "sl_atr_factor", "max_trades_per_day"]
    }
  }
}
```

### LLM-Output (`llm_output.schema.json`)
```json
{
  "type": "object",
  "required": ["decision"],
  "properties": {
    "decision": {
      "enum": ["buy_limit", "sell_limit", "no_trade"]
    },
    "entry": { "type": "number" },
    "stop_loss": { "type": "number" },
    "take_profit": { "type": "number" },
    "confidence": { "type": "number" },
    "valid_until": { "type": "string" },
    "reasons": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

### Signal-Record (`signal_record.schema.json`)
```json
{
  "type": "object",
  "required": ["raw_hash", "feature_snapshot", "llm_input", "llm_output", "final_decision"],
  "properties": {
    "raw_hash": { "type": "string" },
    "feature_snapshot": { "type": "object" },
    "llm_input": { "type": "object" },
    "llm_output": { "type": "object" },
    "final_decision": { "type": "object" }
  }
}
```

## Ablauf- und Fehlerlogik (inkl. Pflichtpunkte)
### 1) API-Key-Fehler klar melden
**Ort:** `provider/alphavantage.py`

- HTTP 401 oder JSON mit `"Error Message"`
- Status `FATAL_CONFIG_ERROR`
- Log-Level `ERROR`
- Scheduler stoppt weitere Fetches
- Meldung im Logfile + State-Datei

State-Format:
```json
{
  "status": "fatal",
  "reason": "invalid_api_key",
  "action": "fix_config_and_restart"
}
```

Kein Retry.

### 2) Rate-Limit-Fälle abfedern (nicht eskalieren)
**Erkennung:**
- HTTP 429
- oder Text `"Thank you for using Alpha Vantage"`

**Verhalten:**
- Log-Level `WARN`
- nächster Fetch erst beim nächsten regulären Intervall
- kein Backoff-Loop
- kein Error-State

State-Eintrag:
```json
{
  "last_fetch": "2026-02-08T16:15",
  "skipped_reason": "rate_limit"
}
```

### 3) Automatische Tageszählung (max_trades_per_day)
**Ort:** `state/trade_counter.py`

- Datum = lokales Datum in Europe/Zurich
- Datei: `/data/state/trade_counter.json`

Struktur:
```json
{
  "date": "2026-02-08",
  "count": 1
}
```

Algorithmus:
- Beim Start: Datum prüfen
- Wenn Datum ≠ heute → count = 0
- Bei jeder akzeptierten Entscheidung ≠ no_trade: count++
- Wenn count ≥ max_trades_per_day: Decision wird hart auf no_trade gesetzt
- Begründung: `"daily_trade_limit_reached"`

## Scheduler-Logik (automatisch aus Nutzungszeiten)
**Ort:** `scheduler.py`

Algorithmus:
- Prüfe Wochentag
- Prüfe Zeitfenster
- Wenn ausserhalb → Sleep bis nächstes Fenster
- Intervall aus Settings:
  - 15min → gültige Minuten: 00, 15, 30, 45
- Runde auf nächste gültige Minute
- Warte + Jitter
- Trigger Fetch
- Kein Cron. Kein Drift.

## Entscheidungsvalidierung (hart)
**Ort:** `decision/validator.py`

Validierungen:
- SL ≠ 0
- TP ≠ 0
- RR ≥ min_rr
- SL-Abstand ≥ ATR × sl_atr_factor
- Tageslimit nicht überschritten

Bei Fehler:
→ no_trade

## Output-Struktur (Dateisystem)
```
data/signals/
└─ 2026/
   └─ 02/
      └─ 08/
         ├─ EURJPY_15min_1615.json
         └─ EURJPY_15min_1630.json
```

Signal-Datei enthält:
- Rohdaten-Hash
- Feature-Snapshot
- LLM-Input
- LLM-Output
- Final-Decision

## Sequenzdiagramm (textuell)
```
Scheduler
   │
   ├─ check_time_window()
   │
   ├─ fetch_market_data()
   │      │
   │      ├─ AlphaVantage API
   │      │     ├─ 200 OK → data
   │      │     ├─ 401 → FATAL STOP
   │      │     └─ 429 → WAIT NEXT SLOT
   │
   ├─ calculate_features()
   │
   ├─ build_llm_input()
   │
   ├─ call_ollama()
   │      │
   │      └─ LLM JSON response
   │
   ├─ validate_decision()
   │      │
   │      ├─ daily_limit_exceeded → no_trade
   │      └─ invalid_rr → no_trade
   │
   ├─ write_signal()
   │
   └─ sleep_until_next_interval()
```
