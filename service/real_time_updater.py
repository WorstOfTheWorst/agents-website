#!/usr/bin/env python3
"""Real‑time updater for agents‑website.

Continuously refreshes:
  * agents status (online/offline/inWork) – from `openclaw status --json`
  * last 5 tasks per agent – from `openclaw tasks list --json`
  * ComfyUI availability – HTTP check to 192.168.0.113:8188

The results are written to the `data/` directory of the website so that
`index.html` can display them instantly.

Run this script as a background service (e.g. via systemd). Adjust the
`sLEEP_INTERVAL` if you need a different refresh rate.
"""

#!/usr/bin/env python3
import json
import os
import subprocess
import time
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")
TASKS_FILE = os.path.join(DATA_DIR, "agents_tasks_detail_human.json")
COMFY_URL = "http://192.168.0.113:8188"
SLEEP_INTERVAL = 120

AGENT_NAMES = {"main": "OpenClaw", "aleksey": "Алексей", "marishka": "Маришка"}


def id_to_name(agent_id: str) -> str:
    return AGENT_NAMES.get(agent_id, agent_id)


def fmt_time(ts_ms):
    if ts_ms is None:
        return None
    return time.strftime("%H:%M", time.localtime(ts_ms // 1000))


def run_cmd(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        return result.stdout
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [run_cmd] ошибка {cmd}: {e}", flush=True)
        return ""


def update_status():
    raw = run_cmd(["openclaw", "status", "--json"])
    status_map = {name: "offline" for name in ["Алексей", "Маришка", "OpenClaw", "ComfyUI"]}

    if raw:
        try:
            data = json.loads(raw)
            for agent in data.get("heartbeat", {}).get("agents", []):
                if agent.get("enabled"):
                    name = id_to_name(agent.get("agentId", ""))
                    if name in status_map:
                        status_map[name] = "online"
            for task in data.get("tasks", {}).get("tasks", []):
                if task.get("status") == "running":
                    name = id_to_name(task.get("agentId", ""))
                    if name in status_map:
                        status_map[name] = "inWork"
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [update_status] ошибка парсинга: {e}", flush=True)

    try:
        r = requests.get(COMFY_URL, timeout=5)
        status_map["ComfyUI"] = "online" if r.status_code == 200 else "offline"
    except Exception:
        status_map["ComfyUI"] = "offline"

    tmp_path = STATUS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(status_map, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, STATUS_FILE)


def update_tasks():
    raw = run_cmd(["openclaw", "tasks", "list", "--json"])
    if not raw:
        return
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [update_tasks] ошибка парсинга: {e}", flush=True)
        return

    transformed = []
    for t in data.get("tasks", []):
        started_ms = t.get("startedAt")
        ended_ms = t.get("endedAt")
        transformed.append({
            "name": id_to_name(t.get("agentId")),
            "label": t.get("label"),
            "status": t.get("status"),
            "startedAt": fmt_time(started_ms),
            "endedAt": fmt_time(ended_ms),
            "durationMin": ((ended_ms - started_ms) // 60000) if started_ms and ended_ms else None,
            "_startedAtMs": started_ms or 0,
        })

    transformed.sort(key=lambda x: x["_startedAtMs"], reverse=True)

    grouped: dict[str, list] = {}
    for entry in transformed:
        grouped.setdefault(entry["name"], []).append(entry)

    result = {
        name: [
            {k: v for k, v in e.items() if k not in ("name", "_startedAtMs")}
            for e in entries[:5]
        ]
        for name, entries in grouped.items()
    }

    tmp_path = TASKS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, TASKS_FILE)


def main():
    while True:
        try:
            update_status()
            update_tasks()
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [main] error: {e}", flush=True)
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main()
