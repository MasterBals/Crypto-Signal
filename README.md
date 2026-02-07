# Forex Signal Cockpit

Dieses Repo stellt ein Docker-Compose Setup bereit, das:

- den **Crypto-Signal** Backend-Container direkt aus dem GitHub-Repo baut,
- ein **Frontend** als separaten Container bereitstellt,
- eine benutzerfreundliche Oberfläche für Forex-Setups inkl. Buy/Sell Empfehlungen bietet.

## Schnellstart

```bash
docker compose up --build
```

Danach ist das Frontend unter `http://localhost:8080` erreichbar. Das Backend läuft auf `http://localhost:8886`.

## Architektur

- **backend**: Wird aus `https://github.com/CryptoSignal/Crypto-Signal.git` gebaut.
- **frontend**: Nginx + statische Web-App. Frontend ruft das Backend über `/api/` auf.

## Anpassung

- API-Endpunkt: Im UI-Feld „API Endpoint“ kann der Request-Pfad angepasst werden.
- Wenn das Backend noch keine Signale liefert, zeigt das UI Demo-Signale an.

