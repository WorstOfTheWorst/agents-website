import json
import os
from pathlib import Path
from fastapi import HTTPException

# Project root (two levels up from this utils file)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def load_json(relative_path: Path):
    file_path = DATA_DIR / relative_path
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{relative_path} not found")
    except json.JSONDecodeError:
        return {}

def save_json(relative_path: Path, data: dict):
    tmp_path = DATA_DIR / f"{relative_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, DATA_DIR / relative_path)
