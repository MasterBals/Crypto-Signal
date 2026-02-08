from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.config import get_settings, update_settings
from app.services.state_cache import get_state, start_scheduler

app = FastAPI(title="EUR/JPY AI Dashboard", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def _startup() -> None:
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
