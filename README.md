# eurjpy-institutional-analyst

Produktionsnahes, webbasiertes Analyse-System für **EUR/JPY** mit Multi-Timeframe-Logik (H4/H1/M15), KI-Wahrscheinlichkeitsbewertung und read-only eToro-Integration.

## Kernprinzipien
- **Nur Analyse** (kein Order-Placement, keine Trade-Execution)
- **Read-only API Integration**
- **ANALYSIS_MODE_ONLY=true** zwingend
- Scheduler alle 5 Minuten

## Start
```bash
docker compose up --build
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000/docs  
AI Engine: http://localhost:8001/docs

## Architektur
- `backend-core`: FastAPI + SQLAlchemy + Analyseengine
- `ai-engine`: LightGBM Training + Inferenz
- `scheduler`: Trigger für periodische Analyse
- `frontend`: React + Tailwind + Lightweight Charts
- `postgres`, `redis`
