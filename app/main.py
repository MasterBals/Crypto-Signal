from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import INSTRUMENTS, get_settings, update_settings
from app.services.db import init_db
from app.services.state_cache import get_state, start_scheduler
from app.services.backup import create_backup

app = FastAPI(title="EUR/JPY AI Dashboard", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


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


@app.get("/api/state", response_class=JSONResponse)
def api_state() -> JSONResponse:
    return JSONResponse(get_state())


@app.get("/api/settings", response_class=JSONResponse)
def api_settings() -> JSONResponse:
    settings = get_settings()
    return JSONResponse(settings.to_dict())


@app.post("/api/settings", response_class=JSONResponse)
def api_update_settings(payload: dict) -> JSONResponse:
    settings = update_settings(payload)
    return JSONResponse(settings.to_dict())


@app.get("/api/instruments", response_class=JSONResponse)
def api_instruments() -> JSONResponse:
    instruments = [
        {
            "key": key,
            "label": value["label"],
            "display_currency": value["display_currency"],
        }
        for key, value in INSTRUMENTS.items()
    ]
    return JSONResponse({"items": instruments})


@app.get("/api/backup", response_class=FileResponse)
def api_backup() -> FileResponse:
    backup_path = create_backup()
    filename = backup_path.name
    return FileResponse(path=str(backup_path), filename=filename)
