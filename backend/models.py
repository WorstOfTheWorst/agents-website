from pydantic import BaseModel, Field, HttpUrl, Extra
from typing import Optional

class ComfyUIConfig(BaseModel):
    """Nested config for ComfyUI URL.
    The URL must be a valid HTTP/HTTPS URL.
    """
    url: HttpUrl = Field(..., description="ComfyUI base URL")

    class Config:
        extra = Extra.forbid  # no additional keys inside comfy_ui

class ConfigModel(BaseModel):
    """Strict model for config.json.
    Only the ``comfy_ui`` section with a valid ``url`` is accepted.
    """
    comfy_ui: ComfyUIConfig

    class Config:
        extra = Extra.forbid  # disallow any other top‑level keys
