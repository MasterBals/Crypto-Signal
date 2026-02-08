from __future__ import annotations

import json
from typing import Any

import requests


def call_ollama(model: str, temperature: float, prompt: str) -> dict[str, Any]:
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    text = payload.get("response", "{}").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"decision": "no_trade", "reasons": ["invalid_llm_output"]}
