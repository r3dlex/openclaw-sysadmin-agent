#!/usr/bin/env bash
# =============================================================================
# Install OpenClaw Watchdog as a macOS LaunchAgent
# =============================================================================
# Generates the plist from the template and loads it into launchd.
#
# Usage:
#   bash scripts/install-watchdog.sh          # Install and start
#   bash scripts/install-watchdog.sh uninstall # Stop and remove
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$REPO_ROOT/scripts/templates/watchdog.plist.template"
PLIST_NAME="com.openclaw.watchdog.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

uninstall() {
    echo "Uninstalling watchdog..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    rm -f "$PLIST_DEST"
    echo "Done."
}

install() {
    # Unload existing if present
    launchctl unload "$PLIST_DEST" 2>/dev/null || true

    echo "Installing watchdog LaunchAgent..."
    echo "  Template: $TEMPLATE"
    echo "  Target:   $PLIST_DEST"

    mkdir -p "$HOME/Library/LaunchAgents"
    mkdir -p "$HOME/.openclaw/logs"

    # Generate plist from template
    sed -e "s|__REPO_ROOT__|$REPO_ROOT|g" \
        -e "s|__HOME__|$HOME|g" \
        "$TEMPLATE" > "$PLIST_DEST"

    # Load
    launchctl load "$PLIST_DEST"
    echo "Watchdog installed and started."
    echo "  Logs: $HOME/.openclaw/logs/watchdog.log"
}

case "${1:-install}" in
    uninstall|remove)
        uninstall
        ;;
    install|*)
        install
        ;;
esac
