# Agents Website

**Agents Website** – небольшое FastAPI‑приложение, которое обслуживает статический веб‑интерфейс дашборда и предоставляет небольшое API для работы с конфигурацией и данными дашборда. Проект отображает статус агентов OpenClaw и доступность ComfyUI.

---

## 📂 Полная структура проекта

```
agents-website/
├─ backend/                     # Код FastAPI‑приложения
│   ├─ main.py                  # Точка входа, монтирует static/, подключает роутеры
│   ├─ models.py                # Pydantic‑модели конфигурации (`ConfigModel`)
│   ├─ utils.py                 # Утилиты для чтения/записи JSON в data/
│   └─ routers/
│       ├─ config.py            # GET/POST `/config` – чтение и запись `config.json`
│       └─ dashboard.py         # GET `/dashboard` – отдаёт `dashboard.json`
├─ static/                      # Статические файлы UI
│   ├─ index.html               # Главная страница дашборда
│   ├─ index_backup.html        # Резервная копия старого шаблона
│   ├─ css/
│   │   └─ styles.css           # Стили сайта (включает блок задач)
│   ├─ js/
│   │   └─ script.js            # Клиентский код, запрашивает `/dashboard` и `/config`
│   └─ assets/                  # Иконки, изображения и т.п.
├─ data/                        # JSON‑файлы, используемые бекендом и сервисом
│   ├─ config.json              # Конфигурация (URL ComfyUI)
│   ├─ dashboard.json           # Объединённый статус и задачи (генерируется сервисом)
│   ├─ status.json              # Текущий статус агентов + ComfyUI ( от `scripts/check_comfy_status.py` )
│   └─ agents_tasks_detail_human.json # Человекочитаемый список последних 5 задач на каждый агент
├─ scripts/                     # Вспомогательные скрипты
│   └─ check_comfy_status.py    # Одноразовая проверка доступности ComfyUI, пишет в `status.json`
├─ service/                     # Фоновый сервис, работающий как systemd‑служба
│   └─ real_time_updater.py     # Каждые 30 с собирает статус агентов, последние задачи и статус ComfyUI,
│                                # записывает `dashboard.json` и `agents_tasks_detail_human.json`
├─ manage_server.sh             # Менеджер systemd‑служб (веб‑сервер + updater) с интерактивным меню
├─ setup_agents_website.sh       # Скрипт создания/перезапуска systemd‑юнита `agents-website.service`
│                                 # (использует `uvicorn backend.main:app` для запуска FastAPI)
├─ INSTRUCTIONS.md               # Полная справка проекта (эта же информация в README)
├─ README.md                     # Текущая документация (вы редактируете её сейчас)
└─ requirements.txt (опционально) # Список Python‑зависимостей (fastapi, uvicorn, pydantic, requests)
```

---

## ⚙️ Что делает каждая часть?

| Каталог/Файл | Описание |
|---|---|
| `backend/` | FastAPI‑приложение. Обслуживает статические файлы и предоставляет API‑эндпоинты `/config` и `/dashboard`. |
| `backend/main.py` | Точка входа, монтирует `static/` и подключает роутеры. |
| `backend/models.py` | Pydantic‑модель `ConfigModel` для валидации `config.json`. |
| `backend/utils.py` | Функции `load_json`/`save_json` для атомарного чтения/записи JSON‑файлов в `data/`. |
| `backend/routers/config.py` | GET `/config` (чтение) и POST `/config` (валидация, сохранение, перезапуск updater‑службы). |
| `backend/routers/dashboard.py` | GET `/dashboard` (отдаёт `data/dashboard.json`). |
| `static/` | Статические файлы UI (HTML, CSS, JS, assets). |
| `static/index.html` | Основная страница дашборда, показывает статус и задачи агентов, форму ввода IP ComfyUI. |
| `static/css/styles.css` | Стили UI, включая блоки статуса и задач. |
| `static/js/script.js` | Клиентский JS: загружает конфиг, сохраняет IP ComfyUI, периодически запрашивает `/dashboard` и обновляет UI. |
| `data/` | Хранилище JSON‑данных, используемое бекендом и сервисом. |
| `data/config.json` | Конфигурация проекта (URL ComfyUI). |
| `data/dashboard.json` | Сводный статус и задачи, генерируется `real_time_updater.py`. |
| `data/status.json` | Текущий статус агентов + ComfyUI (обновляется скриптом `check_comfy_status.py`). |
| `data/agents_tasks_detail_human.json` | Человекочитаемый список последних 5 задач на каждый агент. |
| `scripts/check_comfy_status.py` | Одноразовый скрипт, проверяющий доступность ComfyUI и обновляющий `status.json`. |
| `service/real_time_updater.py` | Фоновый сервис (systemd‑служба `agents-website-updater.service`), каждые 30 сек собирает статусы и задачи, записывает `dashboard.json` и `agents_tasks_detail_human.json`. |
| `manage_server.sh` | Интерактивное меню для управления systemd‑службами `agents-website` и `agents-website-updater` (старт/стоп, логи). |
| `setup_agents_website.sh` | Создаёт/обновляет unit‑файл `/etc/systemd/system/agents-website.service` и перезапускает службу. |
| `INSTRUCTIONS.md` | Полная справка проекта (дублирует README). |
| `requirements.txt` | Перечисление Python‑зависимостей проекта (при наличии). |

---

## ▶️ Как запустить проект

### 1️⃣ Локально (без systemd)

```bash
cd /home/dmitriy/.openclaw/workspace/Projects/agents-website
# Установите зависимости, если их ещё нет
pip install fastapi uvicorn pydantic requests   # или `pip install -r requirements.txt`, если файл существует

# Запустите FastAPI‑приложение
uvicorn backend.main:app --reload   # доступно по http://localhost:8000/
```

### 2️⃣ Через systemd (рекомендовано для постоянной эксплуатации)

```bash
cd /home/dmitriy/.openclaw/workspace/Projects/agents-website

# Установите/перезапустите веб‑службу
sudo ./setup_agents_website.sh

# Включите и запустите сервис‑обновлятор
sudo systemctl enable --now agents-website-updater.service
```

> После этого веб‑интерфейс будет обслуживаться `agents-website.service` на порту 8000, а `real_time_updater.py` будет автоматически обновлять данные в `data/` каждые 30 сек.

### 3️⃣ Одноразовая проверка ComfyUI

```bash
./scripts/check_comfy_status.py
```

Это обновит `data/status.json` без необходимости запускать весь updater‑демон.

---

## 📚 API‑эндпоинты

| Метод | Путь | Описание |
|------|------|----------|
| **GET** | `/config` | Возвращает текущий `config.json` (URL ComfyUI). |
| **POST** | `/config` | Принимает JSON, валидирует через `ConfigModel`, сохраняет и перезапускает `agents-website-updater.service`. |
| **GET** | `/dashboard` | Возвращает объединённый объект `{status, tasks}` из `dashboard.json`. |
| **GET** | `/` (корень) | Отдаёт `static/index.html`. |
| **GET** | `/static/...` | Стат
