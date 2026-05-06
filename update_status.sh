#!/usr/bin/env bash
# Update status.json with simplified statuses: online, offline, inWork
STATUS_FILE="$(dirname "$0")/status.json"

# Fetch full OpenClaw status JSON
JSON=$(openclaw status --json 2>/dev/null)
if [[ -z "$JSON" ]]; then
  echo '{"Алексей":"offline","Маришка":"offline","OpenClaw":"offline"}' > "$STATUS_FILE"
  exit 0
fi

# Initialize all known agents as offline
declare -A statusMap
for name in "Алексей" "Маришка" "OpenClaw"; do
  statusMap["$name"]="offline"
 done

# Helper to map internal agent IDs to display names
id_to_name() {
  case "$1" in
    main) echo "OpenClaw" ;;
    aleksey) echo "Алексей" ;;
    marishka) echo "Маришка" ;;
    *) echo "$1" ;;
  esac
}

# Agents with heartbeat enabled are considered online (if no active tasks they stay online)
online_agents=$(echo "$JSON" | jq -r '.heartbeat.agents[] | select(.enabled == true) | .agentId')
for a in $online_agents; do
  name=$(id_to_name "$a")
  statusMap["$name"]="online"
 done

# Analyze tasks to refine statuses (if task data exists)
if echo "$JSON" | jq -e '.tasks.tasks' >/dev/null 2>&1; then
  # Running tasks => inWork
  echo "$JSON" | jq -r '.tasks.tasks[] | select(.status=="running") | "\(.agentId)"' |
  while read -r agentId; do
    name=$(id_to_name "$agentId")
    statusMap["$name"]="inWork"
  done
  # Queued tasks keep online status (already set)
fi

# Write JSON output
{
  echo "{"
  first=1
  for key in "${!statusMap[@]}"; do
    val="${statusMap[$key]}"
    esc_key=$(printf '%s' "$key" | sed 's/"/\\"/g')
    esc_val=$(printf '%s' "$val" | sed 's/"/\\"/g')
    if [[ $first -eq 1 ]]; then
      first=0
    else
      echo ","
    fi
    printf "  \"%s\":\"%s\"" "$esc_key" "$esc_val"
  done
  echo ""
  echo "}"
} > "$STATUS_FILE"

exit 0
