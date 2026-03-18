#!/usr/bin/env bash
# =============================================================================
# OpenClaw Watchdog — Docker version
# =============================================================================
# Runs independently in a container, checks gateway health every 5 minutes.
# Configuration via environment variables (passed from .env via docker compose).
#
# See: spec/TROUBLESHOOTING.md for common issues
# =============================================================================

set -euo pipefail

LOG_FILE="/logs/watchdog.log"
HEALTH_URL="${OPENCLAW_HEALTH_URL:-http://localhost:9080/health}"
CHECK_INTERVAL="${WATCHDOG_CHECK_INTERVAL:-300}"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

check_gateway() {
    # Try HTTP health endpoint first
    curl -sf --max-time 5 "$HEALTH_URL" &>/dev/null && return 0

    # Fall back to openclaw CLI if available
    if command -v openclaw &>/dev/null; then
        openclaw gateway status 2>/dev/null | grep -qi "running\|started\|online" && return 0
    fi

    return 1
}

restart_gateway() {
    log "Attempting to restart gateway..."

    if ! command -v openclaw &>/dev/null; then
        log "ERROR: openclaw CLI not available in container"
        return 1
    fi

    # Strategy 1: Simple restart
    openclaw gateway stop 2>/dev/null || true
    sleep 2
    openclaw gateway start 2>/dev/null || true
    sleep 5
    if check_gateway; then
        log "Gateway restarted successfully"
        return 0
    fi

    # Strategy 2: Doctor fix
    log "Trying openclaw doctor --fix..."
    openclaw doctor --fix 2>/dev/null || true
    sleep 5
    if check_gateway; then
        log "Doctor --fix resolved issue"
        return 0
    fi

    # Strategy 3: Reinstall
    log "Trying gateway reinstall..."
    openclaw gateway install -f 2>/dev/null || true
    sleep 5
    if check_gateway; then
        log "Gateway reinstalled"
        return 0
    fi

    log "ERROR: Gateway recovery failed after all strategies"
    return 1
}

# --- Main ---
log "OpenClaw Watchdog started (Docker, interval=${CHECK_INTERVAL}s)"

# Wait for gateway to be ready on first run
sleep 30

while true; do
    if ! check_gateway; then
        log "WARNING: Gateway not responding, attempting recovery..."
        restart_gateway
    fi

    sleep "$CHECK_INTERVAL"
done
