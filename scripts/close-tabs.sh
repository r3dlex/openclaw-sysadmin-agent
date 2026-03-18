#!/usr/bin/env bash
# =============================================================================
# Close Unpinned Browser Tabs
# =============================================================================
# Checks if any background cron workers are running. If none are active,
# triggers the Keyboard Maestro macro to close unpinned tabs.
#
# Requires: macOS, Keyboard Maestro, python3
# Macro:    OC_Close_All_Unpinned_Tabs
# =============================================================================

set -euo pipefail

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
REGISTRY="$WORKSPACE/process_registry.json"

# Count active background tasks from the process registry
count_active_tasks() {
    if [[ ! -f "$REGISTRY" ]]; then
        echo 0
        return
    fi

    python3 -c "
import json, sys
try:
    with open('$REGISTRY') as f:
        data = json.load(f)
    tasks = data.get('background_tasks', [])
    running = [t for t in tasks if t.get('status') == 'running']
    print(len(running))
except Exception:
    print(0)
" 2>/dev/null
}

active_tasks=$(count_active_tasks)
himalaya_count=$(pgrep -fc "himalaya_tidy" 2>/dev/null || echo 0)
instagram_count=$(pgrep -fc "instagram" 2>/dev/null || echo 0)

total=$((active_tasks + himalaya_count + instagram_count))

if [[ "$total" -eq 0 ]]; then
    echo "$(date): No crons running — triggering OC_Close_All_Unpinned_Tabs"
    open "kmtrigger://macro=OC_Close_All_Unpinned_Tabs"
else
    echo "$(date): $total cron(s) still running — skipping"
fi
