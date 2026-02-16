# eurjpy-institutional-analyst

Produktionsnahes, webbasiertes Analyse-System für **EUR/JPY** (read-only, keine Orderausführung).

## Wichtiger Betriebsmodus
- `ANALYSIS_MODE_ONLY=true` ist verpflichtend.
- Keine Order-Endpoints.
- Kein Trade-Execution-Flow.

## Stack (nur diese Services)
- `backend-core`
- `ai-engine`
- `frontend`
- `postgres`
- `redis`
- `scheduler`

## Altlasten im Docker/Portainer entfernen
Wenn im Portainer noch alte Container/Services sichtbar sind (z. B. aus `crypto-signal`), einmalig bereinigen:

```bash
docker compose down --remove-orphans --volumes
```

Optional zusätzlich alte Images löschen:

```bash
docker image prune -f
```

## Start
```bash
docker compose up --build
```

## URLs
- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs
- AI Engine: http://localhost:8001/docs
