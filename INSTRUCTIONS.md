# INSTRUCTIONS.md – agents‑website

## Описание проекта
`agents‑website` — статический сайт, служит фронтендом для управления агентами OpenClaw. Хранит JSON‑файлы со статусами задач, скрипты для обновления статуса и простой HTML‑интерфейс.

## Структура каталога
```
agents‑website/
├─ index.html                                 # Главная страница сайта
├─ data/
│   ├─ status.json                          # Текущий статус агентов + ComfyUI
│   └─ agents_tasks_detail_human.json        # Человекочитаемый список последних задач (по 5 на агента)
├─ scripts/
│   ├─ update_status.sh                     # Обновляет data/status.json (агенты + ComfyUI)
│   └─ update_agent_tasks_detail_human.sh    # Обновляет data/agents_tasks_detail_human.json
├─ service/
│   └─ real_time_updater.py                 # Python‑сервис, постоянно обновляет статус, задачи и ComfyUI
├─ check_comfy_status.py                      # (перемещён в scripts/ в рамках сервис‑логики)
├─ setup_agents_website.sh                    # systemd‑служба для быстрой публикации сайта
└─ INSTRUCTIONS.md                            # **Этот файл** – справка по проекту
```

## Назначение ключевых скриптов
- **`setup_agents_website.sh`** – инициализирует проект, копирует шаблоны, проверяет зависимости.
- **`update_agent_tasks_detail_human.sh`** – генерирует человекочитаемый JSON‑отчёт о текущих задачах агентов.
- **`update_status.sh`** – обновляет `status.json` (например, актуальное количество активных агентов, время последнего обновления).

## Как использовать
1. **Первичная инициализация**
   ```bash
   cd /home/dmitriy/.openclaw/workspace/Projects/agents-website
   ./setup_agents_website.sh
   ```
2. **Обновление статусов**
   ```bash
   ./update_status.sh
   ./update_agent_tasks_detail_human.sh
   ```
3. **Запуск сайта**
   Простой способ – открыть `index.html` в браузере или разместить каталог на любом веб‑сервере (nginx, Apache, python -m http.server).

---
*Как и в остальных проектах, после создания/модификации скриптов вносите краткое описание в этот INSTRUCTIONS.md, чтобы быстро восстановить контекст.*