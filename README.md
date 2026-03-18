# OpenClaw Sysadmin Agent

An [OpenClaw](https://docs.openclaw.ai/) agent workspace for autonomous system administration. The agent monitors gateway health, runs maintenance tasks, manages its own memory, and responds to heartbeat polls — all without human intervention.

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/r3dlex/openclaw-sysadmin-agent.git
cd openclaw-sysadmin-agent
cp .env.example .env
# Edit .env with your actual values

# 2. Install the gateway watchdog (pick one)
bash scripts/install-watchdog.sh          # macOS LaunchAgent
# OR
cd watchdog/ && docker compose up -d      # Docker container

# 3. Verify
openclaw gateway status
bash scripts/security-audit.sh
```

## What It Does

- **Gateway monitoring** — Watchdog auto-restarts the OpenClaw gateway after brew upgrades or health failures
- **Daily maintenance** — Version checks, health checks, browser relay verification, security audits
- **Memory management** — Daily logs, long-term memory curation, automatic archival of old files
- **Heartbeat polling** — Periodic checks for emails, calendar, mentions, and proactive tasks
- **Security** — Regular `openclaw security audit --deep` runs and repo-level sensitive data checks

## Repository Structure

```
AGENTS.md              # Agent behavior contract (read by OpenClaw agent)
SOUL.md                # Agent identity and boundaries
PROTOCOL.md            # System maintenance runbook
HEARTBEAT.md           # Periodic task queue
scripts/               # Automation scripts
  ├── watchdog.sh      # Gateway health monitor
  ├── archive.py       # Memory file archiver
  ├── close-tabs.sh    # Browser tab cleanup
  ├── security-audit.sh # Sensitive data checker
  └── install-watchdog.sh # LaunchAgent installer
watchdog/              # Docker-based gateway monitor
spec/                 # Deep-dive documentation
  ├── ARCHITECTURE.md  # How everything fits together
  ├── TROUBLESHOOTING.md # Common issues and fixes
  ├── TESTING.md       # Validation procedures
  └── LEARNINGS.md     # Agent-maintained lessons learned
```

## For Developers

See `CLAUDE.md` for development instructions, `spec/ARCHITECTURE.md` for the full architecture overview, and `spec/TESTING.md` for validation procedures.

## Configuration

All configuration lives in `.env` (gitignored). Copy `.env.example` and fill in your values:

| Variable | Description |
|----------|-------------|
| `BACKUP_DRIVE_PATH` | Path to backup drive |
| `OPENCLAW_PORT` | Gateway port (default: 18789) |
| `WHATSAPP_ALERT_NUMBER` | Phone number for alerts |
| `OPENCLAW_BIN` | Path to openclaw binary |
| `TZ` | Timezone (default: Europe/Berlin) |

See `.env.example` for the full list.

## CI/CD

GitHub Actions run automatically on every push and PR to `main`:

- **Security Audit** — Scans for sensitive data in code and git history
- **Validate** — Lints scripts, checks agent files exist, builds Docker watchdog
- **Docs** — Verifies internal markdown links

See `spec/PIPELINES.md` for details.

## Security

- Sensitive data lives in `.env` (gitignored) — never in committed files
- Runtime data (`logs/`, `archive/`, `.openclaw/`) is gitignored
- GitHub Actions scan every push for leaked secrets (code + history)
- Run `bash scripts/security-audit.sh` locally before every commit
- The agent runs `openclaw security audit --deep` as part of its maintenance protocol

## License

MIT
