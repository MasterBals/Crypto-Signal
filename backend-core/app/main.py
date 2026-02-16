from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.db.init_db import init_db_with_retry

settings = get_settings()

if not settings.analysis_mode_only:
    raise RuntimeError("ANALYSIS_MODE_ONLY must be true")

app = FastAPI(title="eurjpy-institutional-analyst backend-core")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    init_db_with_retry()


@app.api_route("/orders/{path:path}", methods=["POST", "PUT", "DELETE", "PATCH"])
async def block_orders(path: str):
    raise HTTPException(status_code=403, detail="Trade execution disabled in analysis mode")
