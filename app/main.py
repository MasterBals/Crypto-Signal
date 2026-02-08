from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import list_instruments, save_settings, settings
from app.services.backup import create_backup
from app.services.db import init_db
from app.services.state_cache import get_state, start_scheduler

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="EUR/JPY AI Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.on_event("startup")
def _startup() -> None:
    init_db()
    start_scheduler()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/config", response_class=HTMLResponse)
def config_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("config.html", {"request": request})


@app.get("/api/state")
def api_state() -> JSONResponse:
    return JSONResponse(get_state())


@app.get("/api/instruments")
def api_instruments() -> JSONResponse:
    return JSONResponse({"items": list_instruments()})


@app.get("/api/settings")
def api_settings() -> JSONResponse:
    return JSONResponse(settings.to_dict())


@app.post("/api/settings")
async def api_settings_update(request: Request) -> JSONResponse:
    payload: dict[str, Any] = await request.json()
    updated = save_settings(payload)
    return JSONResponse(updated.to_dict())


@app.get("/api/backup")
def api_backup() -> FileResponse:
    backup_path = create_backup()
    return FileResponse(backup_path, filename=backup_path.name, media_type="application/zip")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
