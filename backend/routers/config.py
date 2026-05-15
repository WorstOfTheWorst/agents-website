"""Config router handling GET and POST for config.json.
"""

import subprocess
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pathlib import Path

from ..utils import load_json, save_json
import json
from ..models import ConfigModel

router = APIRouter()

@router.get("/config", response_class=JSONResponse)
async def get_config():
    """Return the current configuration JSON."""
    cfg = load_json(Path("config.json"))
    return cfg

@router.post("/config")
async def update_config(request: Request):
    # Read raw body to handle empty payload gracefully
    raw = await request.body()
    if not raw:
        payload_raw = {}
    else:
        try:
            payload_raw = json.loads(raw)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
    if not isinstance(payload_raw, dict):
        raise HTTPException(status_code=400, detail="Config must be a JSON object")
    # Validate using strict Pydantic model (only comfy_ui.url allowed)
    try:
        config_obj = ConfigModel(**payload_raw)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    # Save the validated config
    save_json(Path("config.json"), config_obj.dict())
    # Restart updater service if present (ignore errors)
    try:
        subprocess.run(
            ["systemctl", "restart", "agents-website-updater.service"],
            check=True,
            timeout=5,
        )
    except Exception as e:
        print(f"Failed to restart updater: {e}")
    return {"detail": "config saved"}
