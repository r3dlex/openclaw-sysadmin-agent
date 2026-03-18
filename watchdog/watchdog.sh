#!/usr/bin/env bash
# OpenClaw Watchdog - Docker version
# Runs independently in container, checks gateway every 5 minutes

LOG_FILE="/logs/watchdog.log"
HOST_gateway="host.docker.internal"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

# Try to find openclaw binary on host
get_openclaw() {
    # Try common paths
    for path in /openclaw /usr/local/bin/openclaw /opt/homebrew/bin/openclaw "$HOME/.local/bin/openclaw"; do
        if [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    # Try using docker host network
    if command -v docker &> /dev/null; then
        # The docker socket is mounted from host
        echo "openclaw"
        return 0
    fi
    
    return 1
}

check_gateway() {
    # Try to reach gateway via curl
    curl -sf --max-time 5 http://localhost:9080/health &>/dev/null && return 0
    
    # Try via openclaw CLI if available
    if command -v openclaw &> /dev/null; then
        openclaw gateway status 2>/dev/null | grep -qi "running\|started\|online" && return 0
    fi
    
    return 1
}

restart_gateway() {
    log "Attempting to restart gateway..."
    
    # Try openclaw CLI
    if command -v openclaw &> /dev/null; then
        openclaw gateway stop 2>/dev/null
        sleep 2
        openclaw gateway start 2>/dev/null
        sleep 5
        
        if check_gateway; then
            log "✅ Gateway restarted successfully"
            return 0
        fi
        
        # Try doctor --fix
        log "Trying openclaw doctor --fix..."
        openclaw doctor --fix 2>/dev/null
        sleep 5
        
        if check_gateway; then
            log "✅ Doctor --fix resolved issue"
            return 0
        fi
        
        # Try reinstall
        log "Trying gateway reinstall..."
        openclaw gateway install -f 2>/dev/null
        sleep 5
        
        if check_gateway; then
            log "✅ Gateway reinstalled"
            return 0
        fi
    fi
    
    log "❌ Could not restart gateway (openclaw not available in container)"
    return 1
}

# Main
log "🐕 OpenClaw Watchdog started (Docker)"

# Wait for gateway to be ready on first run
sleep 30

while true; do
    if ! check_gateway; then
        log "⚠️ Gateway not responding, attempting recovery..."
        restart_gateway
    fi
    
    # Check every 5 minutes
    sleep 300
done
