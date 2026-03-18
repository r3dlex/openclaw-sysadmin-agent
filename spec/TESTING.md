# Testing

> How to verify the sysadmin agent setup is working correctly.

## Quick Health Check

```bash
# 1. Gateway running?
openclaw gateway status

# 2. Watchdog running?
pgrep -f watchdog.sh || echo "Watchdog not running"

# 3. Environment configured?
test -f .env && echo ".env exists" || echo "Missing .env — copy from .env.example"

# 4. Security audit
openclaw security audit --deep
```

## Script Tests

### Watchdog (host)
```bash
# Dry run — check that it starts and logs correctly
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
# Dry run — will report what would be archived
python3 scripts/archive.py
```

### Tab Cleanup
```bash
# Only works on macOS with Keyboard Maestro installed
bash scripts/close-tabs.sh
```

## Validating .env

```bash
# Source and verify key variables are set
source .env
echo "OPENCLAW_BIN: ${OPENCLAW_BIN:-NOT SET}"
echo "OPENCLAW_PORT: ${OPENCLAW_PORT:-NOT SET}"
echo "BACKUP_DRIVE_PATH: ${BACKUP_DRIVE_PATH:-NOT SET}"
echo "TZ: ${TZ:-NOT SET}"
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

Before committing changes:

1. No hardcoded local paths (grep for `/Users/`)
2. No phone numbers or secrets (grep for `+49`, `+1`, passwords)
3. `.env` is gitignored
4. `logs/` and `archive/` are gitignored
5. Run `openclaw security audit --deep`
