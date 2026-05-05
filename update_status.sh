#!/usr/bin/env bash
# Update status.json with detailed agent statuses (online/offline, task info)
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

# Determine online status from heartbeat configuration
online_agents=$(echo "$JSON" | jq -r '.heartbeat.agents[] | select(.enabled == true) | .agentId')
for a in $online_agents; do
  name=$(id_to_name "$a")
  statusMap["$name"]="online"
 done

# Analyze tasks to refine statuses
# For each running or queued task, set a specific status
echo "$JSON" | jq -r '.tasks.tasks[] | select(.status=="running" or .status=="queued") | "\(.agentId)\t\(.label)\t\(.status)"' |
while IFS=$'\t' read -r agentId label taskStatus; do
  name=$(id_to_name "$agentId")
  if [[ "$taskStatus" == "running" ]]; then
    statusMap["$name"]="Работает над: $label"
  else
    statusMap["$name"]="Ожидает задачу"
  fi
 done

# Any agent still marked as "online" without a specific task becomes "Спит"
for name in "Алексей" "Маришка" "OpenClaw"; do
  if [[ "${statusMap[$name]}" == "online" ]]; then
    statusMap["$name"]="Спит"
  fi
 done

# Write JSON file safely (handles Cyrillic keys)
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

