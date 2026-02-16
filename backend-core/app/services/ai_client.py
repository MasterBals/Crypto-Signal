import httpx

from app.core.config import get_settings


async def infer_probability(features: dict) -> float:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{settings.ai_engine_url}/infer", json={"features": features})
            response.raise_for_status()
            return float(response.json().get("probability", 0.5))
    except Exception:
        # Fallback verhindert Analyse-Abbruch falls AI-Service kurzzeitig nicht verfügbar ist.
        return 0.5
