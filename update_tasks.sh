#!/usr/bin/env bash
# Generate tasks.json with recent tasks for each agent (last 3) and current task description
STATUS_FILE="$(dirname "$0")/tasks.json"

# Get tasks JSON
JSON=$(openclaw tasks list --json 2>/dev/null)
if [[ -z "$JSON" ]]; then
  echo '{}' > "$STATUS_FILE"
  exit 0
fi

declare -A tasksMap
# Initialize agents list
for name in "Алексей" "Маришка" "OpenClaw"; do
  tasksMap["$name"]='[]'
done

# Helper to map internal IDs to display names
id_to_name() {
  case "$1" in
    main) echo "OpenClaw" ;;
    aleksey) echo "Алексей" ;;
    marishka) echo "Маришка" ;;
    *) echo "$1" ;;
  esac
}

# Extract tasks, sort by createdAt descending, limit per agent
# We'll collect up to 4 entries (running + 3 recent) per agent
echo "$JSON" | jq -r '.tasks.tasks[] | "\(.agentId)\t\(.label)\t\(.status)\t\(.createdAt)"' | \
  sort -t $'\t' -k4,4nr | \
  while IFS=$'\t' read -r agentId label status createdAt; do
    name=$(id_to_name "$agentId")
    # Build description based on status
    if [[ "$status" == "running" ]]; then
      desc="Текущая: $label"
    else
      desc="$label"
    fi
    # Append to array if less than 4 items
    current=$(echo "${tasksMap[$name]}" | jq -r '. | length')
    if (( current < 4 )); then
      tasksMap["$name"]=$(echo "${tasksMap[$name]}" | jq ". + [\"$desc\"]")
    fi
  done

# Write JSON file safely
cat > "$STATUS_FILE" <<EOF
{
  "Алексей": $(echo "${tasksMap["Алексей"]}"),
  "Маришка": $(echo "${tasksMap["Маришка"]}"),
  "OpenClaw": $(echo "${tasksMap["OpenClaw"]}")
}
EOF
