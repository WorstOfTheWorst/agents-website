#!/usr/bin/env bash
# --------------------------------------------------------------
# manage_server.sh – консольный менеджер для agents-website
#
# Доступные действия:
#   1) Остановить сервер и сервис
#   2) Запустить сервер (systemd‑службу agents-website)
#   3) Запустить сервис‑обновлятор (systemd‑службу agents-website-updater)
#   4) Показать логи (journalctl) для обеих служб, если они есть
#   5) Выход
#
# Требуются привилегии sudo для управления systemd‑службами.
# --------------------------------------------------------------

SERVICE_WEB="agents-website"
SERVICE_UPDATER="agents-website-updater"

function stop_all() {
    echo "Останавливаем веб‑сервер ..."
    sudo systemctl stop "${SERVICE_WEB}.service"
    echo "Останавливаем сервис‑обновлятор ..."
    sudo systemctl stop "${SERVICE_UPDATER}.service"
    echo "Остановлено."
}

function start_server() {
    echo "Запускаем веб‑сервер ..."
    sudo systemctl start "${SERVICE_WEB}.service"
    sudo systemctl status "${SERVICE_WEB}.service" --no-pager
}

function start_updater() {
    echo "Запускаем сервис‑обновлятор ..."
    sudo systemctl start "${SERVICE_UPDATER}.service"
    sudo systemctl status "${SERVICE_UPDATER}.service" --no-pager
}

function show_logs() {
    echo "=== Журналы службы ${SERVICE_WEB} ==="
    sudo journalctl -u "${SERVICE_WEB}.service" --since "1 hour ago" --no-pager || echo "Логи отсутствуют."

    echo -e "\n=== Журналы службы ${SERVICE_UPDATER} ==="
    sudo journalctl -u "${SERVICE_UPDATER}.service" --since "1 hour ago" --no-pager || echo "Логи отсутствуют."
}

while true; do
    echo -e "\n=== Меню управления agents-website ==="
    echo "1) Остановить сервер и сервис"
    echo "2) Запустить сервер"
    echo "3) Запустить сервис‑обновлятор"
    echo "4) Показать логи"
    echo "5) Выход"
    read -p "Выберите действие (1-5): " choice

    case $choice in
        1) stop_all ;;
        2) start_server ;;
        3) start_updater ;;
        4) show_logs ;;
        5) echo "Выход."; exit 0 ;;
        *) echo "Неверный ввод, попробуйте ещё раз." ;;
    esac

done
