# INSTRUCTIONS.md – agents‑website

## Описание проекта
`agents‑website` — статический дашборд, показывающий статус агентов OpenClaw, последние задачи и доступность ComfyUI. Данные берутся из JSON‑файлов, которые обновляются постоянно сервисом `real_time_updater.py`.

## Структура проекта
```
agents‑website/
├─ index.html                     # главная страница (авто‑обновление каждые 30 сек)
├─ data/
│   ├─ status.json                # текущий статус агентов + ComfyUI
│   └─ agents_tasks_detail_human.json  # человекочитаемый список последних 5 задач на каждый агент
├─ scripts/
│   ├─ check_comfy_status.py      # одноразовая проверка доступности ComfyUI (записывает в data/status.json)
│   └─ (deprecated)                # старые bash‑скрипты удалены, обновление теперь выполняет сервис
├─ service/
│   └─ real_time_updater.py       # Python‑сервис, каждые 2 мин обновляет статус, задачи и ComfyUI (ограничение памяти 200 MiB)
├─ setup_agents_website.sh        # systemd‑служба для быстрого развёртывания сайта (Python http.server на порту 8000)
└─ INSTRUCTIONS.md                # этот файл – справка по проекту
```

## Назначение ключевых компонентов
- **`setup_agents_website.sh`** – создаёт/перезапускает systemd‑юнит `agents-website.service`, который обслуживает каталог `index.html` через `python3 -m http.server`.
- **`service/real_time_updater.py`** – постоянно (каждые 120 сек) собирает статус OpenClaw, проверяет ComfyUI (`http://192.168.0.113:8188`) и пишет результаты в `data/status.json` и `data/agents_tasks_detail_human.json` атомарно.
- **`scripts/check_comfy_status.py`** – удобный однократный скрипт для быстрых проверок ComfyUI (если сервис ещё не запущен).

## Как использовать
1. **Инициализация**
   ```bash
   cd /home/dmitriy/.openclaw/workspace/Projects/agents-website
   ./setup_agents_website.sh   # создаст и запустит systemd‑службу
   ```
2. **Запуск постоянного обновления**
   ```bash
   sudo systemctl enable --now agents-website-updater.service   # (unit создаётся вручную, см. docs)
   # либо запустить в фоне:
   python3 service/real_time_updater.py &
   ```
3. **Однократная проверка ComfyUI** (если нужен быстрый чек без сервиса)
   ```bash
   ./scripts/check_comfy_status.py
   ```
4. **Открыть дашборд**
   Откройте в браузере `http://<host>:8000` (по умолчанию порт 8000). Страница будет автоматически перезагружаться каждые 30 сек., отображая актуальный статус и последние задачи.

---
*После любых изменений в скриптах или структуре проекта обновляйте этот файл, чтобы сохранять актуальную документацию.*