#!/usr/bin/env bash
# =============================================================================
# OpenClaw Gateway Watchdog
# =============================================================================
# Monitors gateway health and auto-restarts after brew upgrades.
# Configuration via .env file in the repo root.
#
# Usage:
#   bash scripts/watchdog.sh              # Run directly
#   launchctl load <generated.plist>      # Run as launchd daemon
#
# See: specs/TROUBLESHOOTING.md for common issues
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment
if [[ -f "$REPO_ROOT/.env" ]]; then
    # shellcheck source=/dev/null
    source "$REPO_ROOT/.env"
fi

# Configuration (defaults if .env is missing)
OPENCLAW_BIN="${OPENCLAW_BIN:-/opt/homebrew/bin/openclaw}"
LOCK_FILE="${HOME}/.openclaw/.watchdog.lock"
LOG_FILE="${HOME}/.openclaw/logs/watchdog.log"
LAST_VERSION_FILE="${HOME}/.openclaw/.watchdog_version"
CHECK_INTERVAL="${WATCHDOG_CHECK_INTERVAL:-60}"
BACKUP_HOUR_START="${BACKUP_HOUR_START:-3}"
BACKUP_HOUR_END="${BACKUP_HOUR_END:-5}"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# --- Lock Management ---
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local old_pid
        old_pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            log "Another instance is running (PID $old_pid), exiting"
            exit 1
        fi
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
}

cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# --- Logging ---
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# --- Version Detection ---
get_current_version() {
    "$OPENCLAW_BIN" --version 2>/dev/null | head -1
}

get_initial_version() {
    if [[ -f "$LAST_VERSION_FILE" ]]; then
        cat "$LAST_VERSION_FILE"
    else
        get_current_version > "$LAST_VERSION_FILE" 2>/dev/null
        get_current_version
    fi
}

# --- Health Check ---
check_gateway() {
    local status_output
    status_output=$("$OPENCLAW_BIN" gateway status 2>&1)

    if echo "$status_output" | grep -qE "Runtime: running|RPC probe: ok"; then
        return 0
    fi

    log "Gateway status: $(echo "$status_output" | head -3 | tr '\n' ' ')"
    return 1
}

# --- Restart Strategies (progressive) ---
restart_gateway() {
    log "Gateway not healthy. Attempting restart..."

    # Strategy 1: Simple restart
    "$OPENCLAW_BIN" gateway stop 2>/dev/null || true
    sleep 2
    "$OPENCLAW_BIN" gateway start 2>/dev/null || true
    sleep 5
    if check_gateway; then
        log "Gateway restarted successfully"
        return 0
    fi

    # Strategy 2: Doctor fix
    log "Trying openclaw doctor --fix..."
    "$OPENCLAW_BIN" doctor --fix 2>/dev/null || true
    sleep 5
    if check_gateway; then
        log "Doctor --fix resolved issue"
        return 0
    fi

    # Strategy 3: Brew services restart
    log "Trying brew services restart..."
    brew services restart openclaw 2>/dev/null || true
    sleep 8
    if check_gateway; then
        log "Brew services restart worked"
        return 0
    fi

    # Strategy 4: Reinstall gateway
    log "Trying gateway install..."
    "$OPENCLAW_BIN" gateway install 2>/dev/null || true
    sleep 5
    if check_gateway; then
        log "Gateway reinstalled and started"
        return 0
    fi

    log "ERROR: Gateway recovery failed after all strategies"
    return 1
}

# --- Main Loop ---
main() {
    acquire_lock

    log "OpenClaw Watchdog started (PID $$)"
    local last_version
    last_version=$(get_initial_version)
    log "Initial version: $last_version"

    while true; do
        # Skip during backup hours
        local hour
        hour=$(date +%H)
        if (( hour >= BACKUP_HOUR_START && hour < BACKUP_HOUR_END )); then
            log "Backup hours — skipping health check"
            sleep "$CHECK_INTERVAL"
            continue
        fi

        # Detect version change (brew upgrade)
        local current_version
        current_version=$(get_current_version)
        if [[ "$current_version" != "$last_version" && -n "$current_version" ]]; then
            log "Version changed: $last_version -> $current_version"
            log "Waiting for upgrade to complete..."
            sleep 15
            restart_gateway
            last_version="$current_version"
            echo "$current_version" > "$LAST_VERSION_FILE"
        fi

        # Periodic health check
        if ! check_gateway; then
            log "WARNING: Gateway not healthy, attempting recovery..."
            restart_gateway
        fi

        sleep "$CHECK_INTERVAL"
    done
}

main "$@"
