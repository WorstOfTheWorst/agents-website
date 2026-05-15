from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import subprocess

# Project root (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

app = FastAPI()

# Mount static assets (HTML/CSS/JS) under /static to avoid route clashes
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include API routers from the backend/routers package (no URL prefix)
from .routers import config as config_router, dashboard as dashboard_router
app.include_router(config_router.router)
app.include_router(dashboard_router.router)

@app.get("/", response_class=FileResponse)
async def root():
    """Serve the main UI page (index.html)."""
    return FileResponse(STATIC_DIR / "index.html")


