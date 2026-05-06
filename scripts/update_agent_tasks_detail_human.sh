#!/usr/bin/env bash
# --------------------------------------------------------------
# generate agents_tasks_detail_human.json
# – человекочитаемые timestamps (HH:MM)
# – duration в минутах
# – для каждого агента оставляем только 5 последних задач
# --------------------------------------------------------------

# Путь к файлу‑результату (рядом с этим скриптом)
OUTPUT_FILE="$(dirname "$0")/data/agents_tasks_detail_human.json"

# ------------------------------------------------------------------
# 1. Получаем список всех задач в формате JSON.
# ------------------------------------------------------------------
TASKS_JSON=$(openclaw tasks list --json 2>/dev/null)

# ------------------------------------------------------------------
# 2. Преобразуем через jq:
#    • приводим ID агента к понятному имени
#    • переводим epoch‑мс → HH:MM (локальное время)
#    • считаем длительность в минутах
#    • группируем по агенту и берём только 5 самых «свежих»
# ------------------------------------------------------------------
echo "$TASKS_JSON" | jq '
  .tasks
  # ------------ базовое преобразование каждой задачи ------------
  | map({
        name: (if .agentId == "main"     then "OpenClaw"
               elif .agentId == "aleksey" then "Алексей"
               elif .agentId == "marishka" then "Маришка"
               else .agentId end),
        label: .label,
        status: .status,
        startedAtMs: .startedAt,
        endedAtMs:   .endedAt,
        startedAt: (if .startedAt != null then (.startedAt/1000 | floor | strftime("%H:%M")) else null end),
        endedAt:   (if .endedAt   != null then (.endedAt/1000   | floor | strftime("%H:%M")) else null end),
        durationMin: (if (.startedAt != null and .endedAt != null)
                       then ((.endedAt - .startedAt)/60000) | floor
                       else null end)
    })
  # ------------ сортируем по времени начала (от новых к старым) ------------
  | sort_by(.startedAtMs) | reverse
  # ------------ группируем по агенту и берём только 5 последних ------------
  | group_by(.name)
  | map({
        (.[0].name): (.[0:5] |  # ← 5 последних задач
                      map({label, status, startedAt, endedAt, durationMin}))
    })
  | add
' > "$OUTPUT_FILE.tmp"

# ------------------------------------------------------------------
# 3. Атомарно заменяем старый файл и ставим «читаемые» права
# ------------------------------------------------------------------
mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
chmod 644 "$OUTPUT_FILE"
