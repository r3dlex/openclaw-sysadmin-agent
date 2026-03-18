# Testing

> How to verify the sysadmin agent setup is working correctly.
> Referenced from: `CLAUDE.md`, `AGENTS.md`, `README.md`, `spec/ARCHITECTURE.md`

## Quick Health Check

Run all checks at once:

```bash
bash scripts/security-audit.sh
```

Or individually:

```bash
# 1. Gateway running?
openclaw gateway status

# 2. Watchdog running?
pgrep -f watchdog.sh || echo "Watchdog not running"

# 3. Environment configured?
test -f .env && echo ".env exists" || echo "Missing .env — copy from .env.example"

# 4. Full security audit
openclaw security audit --deep
```

## Script Tests

### Security Audit
```bash
# Checks for sensitive data in git + runs openclaw audit
bash scripts/security-audit.sh
# Exit code 0 = clean, non-zero = issues found
```

### Watchdog (host)
```bash
# Start in background, verify it logs, then stop
bash scripts/watchdog.sh &
sleep 5
tail -5 ~/.openclaw/logs/watchdog.log
kill %1
```

### Watchdog (Docker)
```bash
cd watchdog/
docker compose build
docker compose up -d
sleep 10
docker compose logs --tail=10
docker compose down
```

### Archive Maintenance
```bash
# Reports what would be archived (non-destructive to read)
python3 scripts/archive.py
```

### Tab Cleanup
```bash
# macOS only, requires Keyboard Maestro
bash scripts/close-tabs.sh
```

### Watchdog Installer
```bash
# Install (generates plist from template, loads into launchd)
bash scripts/install-watchdog.sh

# Verify
launchctl list | grep openclaw

# Uninstall
bash scripts/install-watchdog.sh uninstall
```

## Validating .env

```bash
source .env
for var in OPENCLAW_BIN OPENCLAW_PORT BACKUP_DRIVE_PATH TZ WHATSAPP_ALERT_NUMBER; do
  val=$(eval echo "\${$var:-NOT SET}")
  echo "$var: $val"
done
```

## Validating Agent Files

The OpenClaw agent reads these files at session start. Verify they exist and are non-empty:

```bash
for f in AGENTS.md SOUL.md IDENTITY.md USER.md PROTOCOL.md HEARTBEAT.md TOOLS.md; do
  if [ -s "$f" ]; then
    echo "OK: $f"
  else
    echo "MISSING/EMPTY: $f"
  fi
done
```

## Pre-Commit Checklist

Before committing, run the automated audit:

```bash
bash scripts/security-audit.sh
```

This checks:
1. No hardcoded local paths in tracked files
2. No phone numbers or secrets in tracked files
3. `.env` is gitignored
4. `logs/`, `archive/`, `.openclaw/` are gitignored
5. `openclaw security audit --deep` passes

If the audit exits with 0, you're clear to commit.

## CI/CD Pipelines

GitHub Actions run the same checks automatically on push/PR to `main`:

- **Security Audit** — Sensitive data scan (code + git history)
- **Validate** — Script linting, agent file checks, Docker build
- **Docs** — Internal link verification, TODO marker scan

See `spec/PIPELINES.md` for full pipeline documentation.

## Troubleshooting Test Failures

If any test fails, see `spec/TROUBLESHOOTING.md` for step-by-step fixes.
