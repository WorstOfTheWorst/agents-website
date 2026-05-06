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

import json
import os
import subprocess
import time
import requests
import resource  # for memory limiting

# Configuration
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")
TASKS_FILE = os.path.join(DATA_DIR, "agents_tasks_detail_human.json")
COMFY_URL = "http://192.168.0.113:8188"
SLEEP_INTERVAL = 120  # seconds between updates (2 minutes)

# Limit maximum virtual memory to ~200 MiB to avoid OOM kills
MAX_MEMORY_BYTES = 200 * 1024 * 1024
resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))


def run_cmd(cmd: list[str]) -> str:
    """Run a command and return stdout, or empty string on error."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return ""


def update_status():
    """Update `status.json` with simplified agent statuses."""
    raw = run_cmd(["openclaw", "status", "--json"])
    if not raw:
        status_map = {"Алексей": "offline", "Маришка": "offline", "OpenClaw": "offline", "ComfyUI": "offline"}
    else:
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        # default offline
        status_map = {"Алексей": "offline", "Маришка": "offline", "OpenClaw": "offline", "ComfyUI": "offline"}
        # map internal ids to display names
        def id_to_name(agent_id: str) -> str:
            return {
                "main": "OpenClaw",
                "aleksey": "Алексей",
                "marishka": "Маришка",
            }.get(agent_id, agent_id)
        # heartbeat agents considered online
        for agent in data.get("heartbeat", {}).get("agents", []):
            if agent.get("enabled"):
                name = id_to_name(agent.get("agentId", ""))
                if name:
                    status_map[name] = "online"
        # tasks running → inWork
        for task in data.get("tasks", {}).get("tasks", []):
            if task.get("status") == "running":
                name = id_to_name(task.get("agentId", ""))
                if name:
                    status_map[name] = "inWork"
    # ComfyUI check – separate function updates same dict
    try:
        r = requests.get(COMFY_URL, timeout=5)
        comfy_online = r.status_code == 200
    except Exception:
        comfy_online = False
    status_map["ComfyUI"] = "online" if comfy_online else "offline"
    # write file atomically
    tmp_path = STATUS_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(status_map, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, STATUS_FILE)


def update_tasks():
    """Create a human‑readable JSON with the last 5 tasks per agent.
    Mirrors the logic of `update_agent_tasks_detail_human.sh` but in Python.
    """
    raw = run_cmd(["openclaw", "tasks", "list", "--json"])
    if not raw:
        return
    try:
        data = json.loads(raw)
    except Exception:
        return
    tasks = data.get("tasks", [])
    transformed = []
    for t in tasks:
        agent_id = t.get("agentId")
        name = {
            "main": "OpenClaw",
            "aleksey": "Алексей",
            "marishka": "Маришка",
        }.get(agent_id, agent_id)
        # convert ms epoch to HH:MM local time
        def fmt(ts):
            if ts is None:
                return None
            return time.strftime("%H:%M", time.localtime(ts // 1000))
        transformed.append({
            "name": name,
            "label": t.get("label"),
            "status": t.get("status"),
            "startedAt": fmt(t.get("startedAt")),
            "endedAt": fmt(t.get("endedAt")),
            "durationMin": ((t["endedAt"] - t["startedAt"]) // 60000) if t.get("startedAt") and t.get("endedAt") else None,
        })
    # sort newest first
    transformed.sort(key=lambda x: x.get("startedAt"), reverse=True)
    # group by name and keep 5 latest
    grouped = {}
    for entry in transformed:
        name = entry["name"]
        grouped.setdefault(name, []).append(entry)
    result = {name: [
        {k: v for k, v in e.items() if k not in ["name", "startedAtMs", "endedAtMs"]}
    ][:5] for name, entries in grouped.items() for e in [entries]}
    # write atomically
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
            # Log to stdout – in real deployment you may want proper logging.
            print(f"[real_time_updater] error: {e}")
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
