# OpenClaw Sysadmin Agent

An [OpenClaw](https://docs.openclaw.ai/) agent workspace for autonomous system administration. The agent monitors gateway health, runs maintenance tasks, manages its own memory, and responds to heartbeat polls — all without human intervention.

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/r3dlex/openclaw-sysadmin-agent.git
cd openclaw-sysadmin-agent
cp .env.example .env
# Edit .env with your actual values

# 2. Install Python tools (optional — for dev/CI tooling)
pip install .                # Minimal
pip install ".[dotenv]"      # With .env auto-loading
poetry install               # Full dev environment

# 3. Install the gateway watchdog (pick one)
bash scripts/install-watchdog.sh          # macOS LaunchAgent
# OR
cd watchdog/ && docker compose up -d      # Docker container

# 4. Verify
openclaw gateway status
python -m tools.pipeline_runner
```

## What It Does

- **Gateway monitoring** — Watchdog auto-restarts the OpenClaw gateway after brew upgrades or health failures
- **Daily maintenance** — Version checks, health checks, browser relay verification, security audits
- **Memory management** — Daily logs, long-term memory curation, automatic archival of old files
- **Heartbeat polling** — Periodic checks for emails, calendar, mentions, and proactive tasks
- **Security** — Regular `openclaw security audit --deep` runs and repo-level sensitive data checks
- **Inter-agent communication** — Registered on the IAMQ message queue, communicates with peer agents

## Repository Structure

```
pyproject.toml             # Poetry project config (entry points, deps, linting)
tools/                     # Python package
  ├── archive.py           # Memory file archiver (oc-archive)
  ├── security_audit.py    # Sensitive data checker (oc-security-audit)
  ├── iamq.py              # Inter-Agent Message Queue client (oc-iamq)
  └── pipeline_runner/     # CI/CD pipeline runner (oc-pipeline)
      ├── cli.py           # CLI entry point
      ├── runner.py        # Pipeline orchestration
      └── pipelines/       # Individual pipelines
          ├── security.py  # Sensitive data scan
          ├── validate.py  # Lint, agent files, Docker build
          ├── docs.py      # Internal link check
          └── iamq.py      # IAMQ health check
scripts/                   # Shell scripts (macOS-native tasks)
  ├── watchdog.sh          # Gateway health monitor
  ├── close-tabs.sh        # Browser tab cleanup
  ├── security-audit.sh    # Legacy bash audit (still works)
  ├── install-watchdog.sh  # LaunchAgent installer
  └── templates/           # Plist template
watchdog/                  # Docker-based gateway monitor
AGENTS.md                  # Agent behavior contract (read by OpenClaw agent)
SOUL.md                    # Agent identity and boundaries
PROTOCOL.md                # System maintenance runbook
HEARTBEAT.md               # Periodic task queue
spec/                      # Deep-dive documentation
  ├── ARCHITECTURE.md      # How everything fits together
  ├── PIPELINES.md         # CI/CD pipeline documentation
  ├── TROUBLESHOOTING.md   # Common issues and fixes
  ├── TESTING.md           # Validation procedures
  └── LEARNINGS.md         # Agent-maintained lessons learned
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

GitHub Actions run automatically on every push and PR to `main`, powered by `tools/pipeline_runner`:

- **Security Audit** — `python -m tools.pipeline_runner security`
- **Validate** — `python -m tools.pipeline_runner validate`
- **Docs** — `python -m tools.pipeline_runner docs`

Run locally: `python -m tools.pipeline_runner` (all pipelines at once).

See `spec/PIPELINES.md` for details.

## Security

- Sensitive data lives in `.env` (gitignored) — never in committed files
- Runtime data (`logs/`, `archive/`, `.openclaw/`) is gitignored
- GitHub Actions scan every push for leaked secrets (code + history)
- Run `python -m tools.pipeline_runner security` locally before every commit
- The agent runs `openclaw security audit --deep` as part of its maintenance protocol

## License

MIT
