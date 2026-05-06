#!/usr/bin/env bash
# Generate agents_tasks_detail_human.json with human‑readable timestamps (HH:MM) and duration in minutes.
# Output file placed alongside this script.

OUTPUT_FILE="$(dirname "$0")/agents_tasks_detail_human.json"

# Fetch all tasks as JSON.
TASKS_JSON=$(openclaw tasks list --json 2>/dev/null)

# Transform using jq:
# - Keep only completed (any status) tasks.
# - Map agent IDs to display names.
# - Convert startedAt and endedAt from ms epoch to HH:MM (local timezone).
# - Compute duration in minutes (rounded).

echo "$TASKS_JSON" | jq '
  .tasks
  | map({
        name: (if .agentId == "main" then "OpenClaw"
               elif .agentId == "aleksey" then "Алексей"
               elif .agentId == "marishka" then "Маришка"
               else .agentId end),
        label: .label,
        status: .status,
        startedAtMs: .startedAt,
        endedAtMs: .endedAt,
        startedAt: (if .startedAt != null then (.startedAt/1000 | floor | strftime("%H:%M")) else null end),
        endedAt: (if .endedAt != null then (.endedAt/1000 | floor | strftime("%H:%M")) else null end),
        durationMin: (if (.endedAt != null and .startedAt != null) then ((.endedAt - .startedAt)/60000) | floor else null end)
    })
  | group_by(.name)
  | map({ (.[0].name): map({label, status, startedAt, endedAt, durationMin}) })
  | add
' > "$OUTPUT_FILE.tmp"

# Replace atomically and set permissions.
mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
chmod 644 "$OUTPUT_FILE"
