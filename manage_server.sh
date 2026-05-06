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
 
set -uo pipefail
 
SERVICE_WEB="agents-website"
SERVICE_UPDATER="agents-website-updater"
 
# --------------------------------------------------------------
# Вспомогательные функции
# --------------------------------------------------------------
 
# Проверка наличия обязательных инструментов
check_dependencies() {
    if ! command -v systemctl &>/dev/null; then
        echo "Ошибка: systemctl не найден. Скрипт требует systemd." >&2
        exit 1
    fi
    if ! sudo -n true 2>/dev/null; then
        echo "Предупреждение: sudo может запросить пароль при выполнении команд." >&2
    fi
}
 
# Проверка существования службы
service_exists() {
    local svc="$1"
    systemctl list-unit-files "${svc}.service" --no-legend 2>/dev/null | grep -q "${svc}.service"
}
 
# Проверка, запущена ли служба
service_is_active() {
    local svc="$1"
    systemctl is-active --quiet "${svc}.service" 2>/dev/null
}
 
# Остановка одной службы с проверкой состояния
stop_service() {
    local svc="$1"
    if ! service_exists "${svc}"; then
        echo "  [!] Служба ${svc} не найдена, пропускаем."
        return 0
    fi
    if service_is_active "${svc}"; then
        echo "  Останавливаем ${svc} ..."
        if sudo systemctl stop "${svc}.service"; then
            echo "  [OK] ${svc} остановлена."
        else
            echo "  [ERR] Не удалось остановить ${svc}." >&2
            return 1
        fi
    else
        echo "  [--] ${svc} уже остановлена."
    fi
}
 
# Запуск одной службы с проверкой состояния
start_service() {
    local svc="$1"
    if ! service_exists "${svc}"; then
        echo "  [!] Служба ${svc} не найдена." >&2
        return 1
    fi
    if service_is_active "${svc}"; then
        echo "  [--] ${svc} уже запущена."
    else
        echo "  Запускаем ${svc} ..."
        if sudo systemctl start "${svc}.service"; then
            echo "  [OK] ${svc} запущена."
        else
            echo "  [ERR] Не удалось запустить ${svc}." >&2
            return 1
        fi
    fi
    echo ""
    sudo systemctl status "${svc}.service" --no-pager || true
}
 
# --------------------------------------------------------------
# Основные действия меню
# --------------------------------------------------------------
 
stop_all() {
    echo "=== Остановка служб ==="
    stop_service "${SERVICE_WEB}"
    stop_service "${SERVICE_UPDATER}"
    echo "=== Готово ==="
}
 
start_server() {
    echo "=== Запуск веб‑сервера ==="
    start_service "${SERVICE_WEB}"
}
 
start_updater() {
    echo "=== Запуск сервиса‑обновлятора ==="
    start_service "${SERVICE_UPDATER}"
}
 
show_logs() {
    echo "=== Журналы службы ${SERVICE_WEB} (за последний час) ==="
    if service_exists "${SERVICE_WEB}"; then
        sudo journalctl -u "${SERVICE_WEB}.service" --since "1 hour ago" --no-pager 2>/dev/null \
            || echo "  Логи отсутствуют."
    else
        echo "  Служба ${SERVICE_WEB} не найдена."
    fi
 
    printf "\n=== Журналы службы ${SERVICE_UPDATER} (за последний час) ===\n"
    if service_exists "${SERVICE_UPDATER}"; then
        sudo journalctl -u "${SERVICE_UPDATER}.service" --since "1 hour ago" --no-pager 2>/dev/null \
            || echo "  Логи отсутствуют."
    else
        echo "  Служба ${SERVICE_UPDATER} не найдена."
    fi
}
 
# --------------------------------------------------------------
# Точка входа
# --------------------------------------------------------------
 
check_dependencies
 
while true; do
    printf "\n=== Меню управления agents-website ===\n"
    echo "1) Остановить сервер и сервис"
    echo "2) Запустить сервер"
    echo "3) Запустить сервис‑обновлятор"
    echo "4) Показать логи"
    echo "5) Выход"
    read -rp "Выберите действие (1-5): " choice
 
    case "${choice}" in
        1) stop_all ;;
        2) start_server ;;
        3) start_updater ;;
        4) show_logs ;;
        5) echo "Выход."; exit 0 ;;
        *) echo "Неверный ввод, попробуйте ещё раз." ;;
    esac
done
