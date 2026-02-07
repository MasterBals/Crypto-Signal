# Forex Signal Cockpit

Dieses Repo stellt ein Docker-Compose Setup bereit, das:

- den **Crypto-Signal** Backend-Container direkt aus dem GitHub-Repo lädt (ohne `git` im Build),
- ein **Frontend** als separaten Container bereitstellt,
- eine benutzerfreundliche Oberfläche für Forex-Setups inkl. Buy/Sell Empfehlungen bietet.

## Schnellstart

```bash
docker compose up --build
```

Danach ist das Frontend unter `http://localhost:8887` erreichbar. Das Backend läuft intern auf `http://backend:8886`.

## Architektur

- **backend**: Wird über ein Dockerfile gebaut, das den Upstream als ZIP lädt.
- **frontend**: Nginx + statische Web-App. Frontend ruft das Backend über `/api/` auf.

## Anpassung

- API-Endpunkt: Im UI-Feld „API Endpoint“ kann der Request-Pfad angepasst werden.
- Backend-Branch: In `docker-compose.yml` kann `CRYPTOSIGNAL_REF` (z. B. `main`) gesetzt werden.
- Wenn das Backend noch keine Signale liefert, zeigt das UI Demo-Signale an.

## Hinweis zu Build-Umgebungen ohne git

Der Backend-Build lädt den Upstream als ZIP, damit kein `git` auf dem Build-Host benötigt wird.
Wenn dennoch ein Fehler wie „git: executable file not found in $PATH“ auftaucht, bitte sicherstellen,

- dass `docker-compose.yml` aus diesem Repo genutzt wird (kein alter Compose-Stack mit Git-URL),
- und die Build-Cache/Builder-Instanz neu erstellt wird, falls Docker eine alte Git-Quelle cached.

