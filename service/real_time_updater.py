#!/usr/bin/env python3
"""Фоновый сервис обновления данных для agents-website.

Периодически обновляет:
  * статус агентов (online/offline/inWork) — через `openclaw status --json`
  * последние 5 задач каждого агента — через `openclaw tasks list --json`
  * доступность ComfyUI — HTTP-запрос на 192.168.0.113:8188

Результаты записываются в директорию `data/` сайта, откуда `index.html`
читает их и отображает в реальном времени.

Запускается как фоновый сервис (например, через systemd).
Частоту обновления можно изменить через константу `SLEEP_INTERVAL`.
"""

import json
import os
import subprocess
import time
import requests
import datetime

# Корень проекта — на уровень выше директории со скриптом
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Директория с JSON-файлами, которые читает фронтенд
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
# Файл со статусами агентов (используется только как константа, запись идёт в dashboard.json)
STATUS_FILE = os.path.join(DATA_DIR, "status.json")
# Файл с детализированными задачами агентов в человекочитаемом формате
TASKS_FILE = os.path.join(DATA_DIR, "agents_tasks_detail_human.json")

# URL ComfyUI по умолчанию, если конфиг недоступен
COMFY_DEFAULT_URL = "http://192.168.0.113:8188"
# Интервал между обновлениями в секундах
SLEEP_INTERVAL = 30

# Соответствие внутренних ID агентов их отображаемым именам
AGENT_NAMES = {"main": "OpenClaw", "aleksey": "Алексей", "alexey": "Алексей", "marishka": "Маришка"}

# Полный путь к бинарнику OpenClaw
OPENCLAW_BIN = "/usr/bin/openclaw"


def get_comfy_url() -> str:
    """Читает URL ComfyUI из data/config.json. Если файл недоступен — возвращает дефолтный URL."""
    config_path = os.path.join(DATA_DIR, "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("comfy_ui", {}).get("url", COMFY_DEFAULT_URL)
    except Exception:
        # Конфиг отсутствует или повреждён — используем значение по умолчанию
        return COMFY_DEFAULT_URL


def id_to_name(agent_id: str) -> str:
    """Преобразует внутренний ID агента в отображаемое имя."""
    return AGENT_NAMES.get(agent_id, agent_id)


def fmt_time(ts_ms):
    """Конвертирует timestamp в миллисекундах в строку формата ЧЧ:ММ.
    Возвращает None, если timestamp не задан.
    """
    if ts_ms is None:
        return None
    return time.strftime("%H:%M", time.localtime(ts_ms // 1000))


def run_cmd(cmd: list[str]) -> str:
    """Выполняет команду OpenClaw CLI и возвращает stdout.

    Если скрипт запущен от root (например, через systemd), команда
    выполняется от имени пользователя `dmitriy`, чтобы OpenClaw читал
    корректную конфигурацию и видел задачи агентов.
    """
    # Нормализуем команду: убираем "openclaw" из начала, оставляем только аргументы
    if cmd and cmd[0] == "openclaw":
        args = cmd[1:]
    else:
        args = cmd

    # Если текущий пользователь — root, понижаем привилегии через sudo
    if os.geteuid() == 0:
        full_cmd = ["sudo", "-u", "dmitriy", OPENCLAW_BIN] + args
    else:
        full_cmd = [OPENCLAW_BIN] + args

    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, check=True, timeout=60)
        return result.stdout
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [run_cmd] ошибка {cmd}: {e}", flush=True)
        return ""


def get_agent_status() -> dict:
    """Возвращает словарь со статусами агентов OpenClaw (без ComfyUI).

    Статусы: offline / online / inWork.
    Агент считается inWork, если у него есть задача со статусом running.
    """
    raw = run_cmd(["openclaw", "status", "--json"])

    # По умолчанию все агенты offline
    status_map = {name: "offline" for name in ["Алексей", "Маришка", "OpenClaw"]}

    if raw:
        try:
            data = json.loads(raw)

            # Помечаем агентов как online по heartbeat
            for agent in data.get("heartbeat", {}).get("agents", []):
                if agent.get("enabled"):
                    name = id_to_name(agent.get("agentId", ""))
                    if name in status_map:
                        status_map[name] = "online"

            # Если у агента есть активная задача — переводим в inWork
            for task in data.get("tasks", {}).get("tasks", []):
                if task.get("status") == "running":
                    name = id_to_name(task.get("agentId", ""))
                    if name in status_map:
                        status_map[name] = "inWork"

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [get_agent_status] ошибка парсинга: {e}", flush=True)

    return status_map


def check_comfy_ui() -> str:
    """Проверяет доступность ComfyUI HTTP-запросом.
    Возвращает 'online' при HTTP 200, иначе 'offline'.
    """
    try:
        url = get_comfy_url()
        r = requests.get(url, timeout=5)
        return "online" if r.status_code == 200 else "offline"
    except Exception:
        # Сервер недоступен или превышен таймаут
        return "offline"


def get_comfyui_tasks() -> list[dict]:
    """Читает задачи ComfyUI из SMMProject/tasks.json и возвращает их в формате дашборда.

    Формат каждой записи:
        {
            "label": <файл воркфлоу>,
            "status": <статус>,
            "startedAt": <ЧЧ:ММ>
        }
    Возвращает не более 5 самых свежих задач.
    """
    # Путь до tasks.json соседнего проекта SMMProject
    tasks_path = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "SMMProject", "tasks.json"))

    if not os.path.isfile(tasks_path):
        return []

    try:
        with open(tasks_path, "r", encoding="utf-8") as f:
            raw_tasks = json.load(f)
    except Exception as exc:
        print(f"[real_time_updater] Не удалось прочитать {tasks_path}: {exc}", flush=True)
        return []

    entries = []
    for t in raw_tasks:
        start_str = t.get("start_time")
        started_at = None
        started_ms = 0

        if start_str:
            try:
                # Парсим время запуска задачи из строки формата "ГГГГ-ММ-ДД ЧЧ:ММ:СС"
                dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                started_at = dt.strftime("%H:%M")
                started_ms = int(dt.timestamp() * 1000)
            except Exception:
                pass

        entries.append({
            "label": t.get("workflow_file"),
            "status": t.get("status"),
            "startedAt": started_at,
            "date": datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%y") if start_str else None,
            "_startedAtMs": started_ms,
        })

    # Сортируем от новых к старым и берём только 5 последних
    entries.sort(key=lambda x: x["_startedAtMs"], reverse=True)
    # Убираем внутреннее поле перед возвратом
    return [{k: v for k, v in entry.items() if k != "_startedAtMs"} for entry in entries[:5]]


def get_tasks() -> dict:
    """Получает последние 5 задач каждого агента через `openclaw tasks list --json`.

    Возвращает словарь вида:
        { "Имя агента": [ { задача1 }, { задача2 }, ... ] }
    """
    raw = run_cmd(["openclaw", "tasks", "list", "--json"])
    if not raw:
        return {}

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [get_tasks] ошибка парсинга: {e}", flush=True)
        return {}

    # Преобразуем сырые задачи в удобный формат
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
            "date": datetime.datetime.fromtimestamp(started_ms / 1000).strftime("%d.%m.%y") if started_ms else None,
            # Длительность в минутах — только если обе временные метки присутствуют
            "durationMin": ((ended_ms - started_ms) // 60000) if started_ms and ended_ms else None,
            "error": t.get("error"),
            "_startedAtMs": started_ms or 0,
        })

    # Сортируем все задачи от новых к старым
    transformed.sort(key=lambda x: x["_startedAtMs"], reverse=True)

    # Группируем задачи по имени агента
    grouped: dict[str, list] = {}
    for entry in transformed:
        grouped.setdefault(entry["name"], []).append(entry)

    # Оставляем не более 5 задач на агента, убираем служебные поля
    result = {
        name: [
            {
                k: v
                for k, v in e.items()
                if k not in ("name", "_startedAtMs")
                and (k != "error" or (e.get("name") in ("OpenClaw", "Маришка", "Алексей") and v))
            }
            for e in entries[:5]
        ]
        for name, entries in grouped.items()
    }
    return result


def write_dashboard():
    """Собирает статусы и задачи, записывает итоговый dashboard.json атомарно.

    Запись идёт сначала во временный файл (.tmp), затем он атомарно
    переименовывается — чтобы фронтенд никогда не прочитал частично записанный файл.
    """
    # Получаем статусы агентов и ComfyUI
    status_map = get_agent_status()
    status_map["ComfyUI"] = check_comfy_ui()

    # Получаем задачи агентов
    tasks_map = get_tasks()
    # Получаем задачи ComfyUI и добавляем их в общий словарь
    tasks_map["ComfyUI"] = get_comfyui_tasks()

    data = {"status": status_map, "tasks": tasks_map}

    dashboard_path = os.path.join(DATA_DIR, "dashboard.json")
    tmp_path = dashboard_path + ".tmp"

    # Пишем во временный файл, затем атомарно заменяем основной
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, dashboard_path)


def main():
    """Основной цикл: обновляет дашборд каждые SLEEP_INTERVAL секунд."""
    while True:
        try:
            write_dashboard()
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [main] ошибка: {e}", flush=True)
        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main()