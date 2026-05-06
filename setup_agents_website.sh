#!/usr/bin/env bash
# Script to (re)install the agents-website systemd service with safe pre/stop hooks.
# Run as root (sudo) or with sufficient privileges.

SERVICE_FILE="/etc/systemd/system/agents-website.service"

cat > "$SERVICE_FILE" <<'EOF'
[Unit]
Description=Agents static site server
After=network.target

[Service]
Type=simple
# Принудительно освобождаем порт 8000, если он занят
ExecStartPre=-/usr/bin/fuser -k 8000/tcp
WorkingDirectory=/home/dmitriy/.openclaw/workspace/Projects/agents-website
ExecStart=/usr/bin/python3 -m http.server 8000 --bind 0.0.0.0
ExecStopPost=/bin/kill -9 $MAINPID
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd daemon to recognize changes
systemctl daemon-reload

# Restart the service (will stop any existing instance first)
systemctl restart agents-website

# Show status
systemctl status agents-website --no-pager
