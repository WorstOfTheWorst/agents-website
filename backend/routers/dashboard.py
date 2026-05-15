"""Dashboard router for FastAPI.
Provides the combined status and tasks endpoint.
"""

import json
from fastapi import APIRouter, HTTPException
from pathlib import Path
from fastapi.responses import JSONResponse

from ..utils import DATA_DIR

router = APIRouter()

@router.get("/dashboard", response_class=JSONResponse)
async def dashboard():
    """Return combined status and tasks from the dashboard JSON file.
    If the file is missing, return empty structures.
    """
    dashboard_path = DATA_DIR / "dashboard.json"
    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"status": {}, "tasks": {}}
