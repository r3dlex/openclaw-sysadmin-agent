# Testing

> How to verify the sysadmin agent setup is working correctly.
> Referenced from: `CLAUDE.md`, `AGENTS.md`, `README.md`, `spec/ARCHITECTURE.md`

## Quick Health Check

Run all pipelines at once:

```bash
python -m tools.pipeline_runner
```

Or run individual checks:

```bash
# 1. Gateway running?
openclaw gateway status

# 2. Watchdog running?
pgrep -f watchdog.sh || echo "Watchdog not running"

# 3. Environment configured?
test -f .env && echo ".env exists" || echo "Missing .env — copy from .env.example"

# 4. Full security audit (with openclaw CLI)
python -m tools.security_audit
```

## Pipeline Tests

### Run All Pipelines
```bash
python -m tools.pipeline_runner
# Runs: security, validate, docs
# Exit code 0 = all passed, non-zero = failures
```

### Security Pipeline Only
```bash
python -m tools.pipeline_runner security
# Checks: hardcoded paths, phone numbers, secrets, gitignore, git history
```

### Validate Pipeline Only
```bash
python -m tools.pipeline_runner validate
# Checks: shellcheck, ruff, agent files, spec files, Docker build
```

### Docs Pipeline Only
```bash
python -m tools.pipeline_runner docs
# Checks: internal markdown links, TODO markers
```

## Script Tests

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
python -m tools.archive
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

Before committing, run:

```bash
python -m tools.pipeline_runner
```

This checks:
1. No hardcoded local paths in tracked files
2. No phone numbers or secrets in tracked files
3. `.env`, `logs/`, `archive/`, `.openclaw/` are gitignored
4. Shell scripts pass shellcheck (non-blocking)
5. Python code passes syntax check and ruff (non-blocking)
6. All required agent and spec files exist
7. Internal markdown links resolve
8. No stale TODO markers in docs

If all pipelines pass, you're clear to commit.

## CI/CD Pipelines

GitHub Actions run the same pipelines automatically on push/PR to `main`:

- **Security Audit** — `python -m tools.pipeline_runner security`
- **Validate** — `python -m tools.pipeline_runner validate` + Docker build
- **Docs** — `python -m tools.pipeline_runner docs`

See `spec/PIPELINES.md` for full pipeline documentation.

## Troubleshooting Test Failures

If any test fails, see `spec/TROUBLESHOOTING.md` for step-by-step fixes.
