#!/usr/bin/env python3
import json
import os
import requests


def main():
    # Читаем IP адрес ComfyUI из конфигурационного файла (data/config.json)
    config_path = os.path.join(os.path.dirname(__file__), "..", "data", "config.json")
    default_url = "http://192.168.0.113:8188"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            url = cfg.get("comfy_ui", {}).get("url", default_url)
    except Exception:
        url = default_url
    try:
        resp = requests.get(url, timeout=5)
        online = resp.status_code == 200
    except Exception:
        online = False
    status = "online" if online else "offline"

    # Path to the website data/status.json (relative to this script)
    status_path = os.path.join(os.path.dirname(__file__), "..", "data", "status.json")
    try:
        with open(status_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data["ComfyUI"] = status
    # Write atomically to avoid corrupting the file if the script crashes mid‑write
    tmp_path = status_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, status_path)
    print(f"ComfyUI status updated: {status}")


if __name__ == "__main__":
    main()

