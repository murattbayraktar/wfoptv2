#!/usr/bin/env bash
#
# WFOpt gelistirme sunucularini yonetir (macOS).
#
# Kullanim:
#   ./dev.sh           # varsayilan: start
#   ./dev.sh start
#   ./dev.sh stop
#   ./dev.sh restart
#   ./dev.sh status

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$ROOT/bank_forecast"
FRONT_DIR="$ROOT/bank_forecast/frontend"
UVICORN="$API_DIR/venv/bin/uvicorn"
PID_FILE="$ROOT/.dev-pids"
API_LOG="$ROOT/.dev-api.log"
FRONT_LOG="$ROOT/.dev-frontend.log"

ACTION="${1:-start}"

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; GRAY=$'\033[90m'; NC=$'\033[0m'

get_saved_pids() {
    [ -f "$PID_FILE" ] || return 0
    tr ',' '\n' < "$PID_FILE" | grep -E '^[0-9]+$' || true
}

is_running() {
    kill -0 "$1" 2>/dev/null
}

start_services() {
    local saved running=()
    saved="$(get_saved_pids)"
    while IFS= read -r p; do
        [ -n "$p" ] && is_running "$p" && running+=("$p")
    done <<< "$saved"

    if [ "${#running[@]}" -gt 0 ]; then
        echo ""
        echo "  ${YELLOW}Servisler zaten calisiyor (PID: $(IFS=,; echo "${running[*]}"))." "$NC"
        echo "  ${GRAY}Yeniden baslatmak icin:  ./dev.sh restart${NC}"
        echo ""
        return
    fi
    rm -f "$PID_FILE"

    if [ ! -x "$UVICORN" ]; then
        echo ""
        echo "  ${RED}[HATA] Uvicorn bulunamadi: $UVICORN${NC}"
        echo "  ${GRAY}venv olusturup pip install -r requirements.txt calistirin.${NC}"
        echo ""
        return
    fi

    ( cd "$API_DIR" && exec "$UVICORN" api.main:app --reload --reload-dir api --reload-dir src --reload-dir config --port 8000 ) > "$API_LOG" 2>&1 &
    local api_pid=$!

    ( cd "$FRONT_DIR" && exec npm run dev </dev/null ) > "$FRONT_LOG" 2>&1 &
    local front_pid=$!

    echo "${api_pid},${front_pid}" > "$PID_FILE"

    echo ""
    echo "  ${GREEN}Servisler baslatildi${NC}"
    echo "  ${CYAN}API       -> http://localhost:8000  (PID $api_pid)${NC}"
    echo "  ${CYAN}Frontend  -> http://localhost:5173  (PID $front_pid)${NC}"
    echo ""
    echo "  ${GRAY}Loglar:  $API_LOG , $FRONT_LOG${NC}"
    echo "  ${GRAY}Durdurmak icin:  ./dev.sh stop${NC}"
    echo ""
}

stop_services() {
    local pids
    pids="$(get_saved_pids)"
    if [ -z "$pids" ]; then
        echo ""
        echo "  ${YELLOW}Calisir durumda kayitli servis yok.${NC}"
        echo ""
        return
    fi
    echo ""
    while IFS= read -r p; do
        [ -n "$p" ] || continue
        if is_running "$p"; then
            pkill -TERM -P "$p" 2>/dev/null || true
            kill -TERM "$p" 2>/dev/null || true
            sleep 0.5
            if is_running "$p"; then
                pkill -KILL -P "$p" 2>/dev/null || true
                kill -KILL "$p" 2>/dev/null || true
            fi
            echo "  ${RED}Durduruldu  PID $p${NC}"
        else
            echo "  ${GRAY}Zaten durmustu  PID $p${NC}"
        fi
    done <<< "$pids"
    rm -f "$PID_FILE"
    echo "  ${GREEN}Tum servisler durduruldu.${NC}"
    echo ""
}

status_services() {
    local pids
    pids="$(get_saved_pids)"
    echo ""
    if [ -z "$pids" ]; then
        echo "  ${YELLOW}Kayitli servis yok.${NC}"
        echo ""
        return
    fi
    while IFS= read -r p; do
        [ -n "$p" ] || continue
        if is_running "$p"; then
            local cmd
            cmd="$(ps -o comm= -p "$p" 2>/dev/null || echo '?')"
            echo "  ${GREEN}CALISIYOR   PID $p   $cmd${NC}"
        else
            echo "  ${RED}DURMUS      PID $p   (surec bulunamadi)${NC}"
        fi
    done <<< "$pids"
    echo ""
}

case "$ACTION" in
    start)   start_services ;;
    stop)    stop_services ;;
    restart) stop_services; sleep 0.8; start_services ;;
    status)  status_services ;;
    *)
        echo "Kullanim: $0 [start|stop|restart|status]"
        exit 1
        ;;
esac
