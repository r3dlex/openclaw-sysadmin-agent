#!/usr/bin/env bash
# =============================================================================
# OpenClaw Security Audit
# =============================================================================
# Runs a deep security audit and checks for sensitive data in the repo.
#
# Usage:
#   bash scripts/security-audit.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== OpenClaw Security Audit ==="
echo "Date: $(date)"
echo ""

# --- Check for sensitive data in tracked files ---
echo "--- Checking for sensitive data in git-tracked files ---"
ISSUES=0

# Check for hardcoded home directories
if git -C "$REPO_ROOT" grep -n '/Users/' -- ':(exclude).gitignore' ':(exclude)scripts/security-audit.sh' ':(exclude)spec/TESTING.md' 2>/dev/null | grep -v 'template\|example\|TEMPLATE\|__HOME__\|grep.*Users' | head -20; then
    echo "WARNING: Found hardcoded /Users/ paths in tracked files"
    ISSUES=$((ISSUES + 1))
else
    echo "OK: No hardcoded user paths found"
fi

# Check for phone numbers (basic pattern)
if git -C "$REPO_ROOT" grep -nE '\+[0-9]{10,}' -- ':(exclude).env.example' 2>/dev/null | head -10; then
    echo "WARNING: Found possible phone numbers in tracked files"
    ISSUES=$((ISSUES + 1))
else
    echo "OK: No phone numbers found"
fi

# Check for common secret patterns
if git -C "$REPO_ROOT" grep -nEi '(api_key|secret_key|password|token)\s*=' -- '*.py' '*.sh' '*.md' 2>/dev/null | grep -v 'example\|template\|dummy\|placeholder\|spec/' | head -10; then
    echo "WARNING: Found possible secrets in tracked files"
    ISSUES=$((ISSUES + 1))
else
    echo "OK: No secrets patterns found"
fi

# Check .env is gitignored
if git -C "$REPO_ROOT" check-ignore .env >/dev/null 2>&1; then
    echo "OK: .env is gitignored"
else
    echo "CRITICAL: .env is NOT gitignored!"
    ISSUES=$((ISSUES + 1))
fi

# Check logs/ and archive/ are gitignored
for dir in logs archive .openclaw; do
    if git -C "$REPO_ROOT" check-ignore "$dir/" >/dev/null 2>&1; then
        echo "OK: $dir/ is gitignored"
    else
        echo "WARNING: $dir/ is NOT gitignored"
        ISSUES=$((ISSUES + 1))
    fi
done

echo ""

# --- Run openclaw security audit if available ---
echo "--- OpenClaw Security Audit ---"
OPENCLAW_BIN="${OPENCLAW_BIN:-openclaw}"
if command -v "$OPENCLAW_BIN" &>/dev/null; then
    "$OPENCLAW_BIN" security audit --deep 2>&1 || echo "openclaw security audit returned non-zero"
else
    echo "SKIP: openclaw CLI not found at $OPENCLAW_BIN"
fi

echo ""
echo "=== Audit complete: $ISSUES issue(s) found ==="
exit "$ISSUES"
