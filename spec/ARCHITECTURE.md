# Architecture

> How the sysadmin agent workspace is organized and why.
> Referenced from: `CLAUDE.md`, `AGENTS.md`, `README.md`

## Overview

This repository is an **OpenClaw agent workspace** — a self-contained environment where an AI agent acts as a system administrator for a macOS host running the [OpenClaw](https://docs.openclaw.ai/) gateway.

```
┌─────────────────────────────────────────────────┐
│  OpenClaw Gateway (localhost:18789)              │
│  ├── WhatsApp / Telegram / Discord / iMessage    │
│  ├── Heartbeat polling                           │
│  └── Skill execution                             │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Sysadmin Agent Workspace (this repo)            │
│  ├── AGENTS.md      → Agent behavior contract    │
│  ├── SOUL.md        → Identity & tone            │
│  ├── PROTOCOL.md    → Maintenance runbook        │
│  ├── HEARTBEAT.md   → Periodic task queue        │
│  ├── tools/         → Python tooling (Poetry)    │
│  ├── scripts/       → Shell scripts (macOS)      │
│  ├── watchdog/      → Gateway health monitor     │
│  └── spec/          → Architecture docs          │
└──────────┬───────────────────┬──────────────────┘
           │                   │
┌──────────▼──────────┐        │
│  IAMQ (Elixir/OTP)  │        │
│  :18790 HTTP         │        │
│  :18793 WebSocket    │        │
│  Agent discovery &   │        │
│  inter-agent msgs    │        │
└─────────────────────┘        │
                   ┌───────────▼──────────────────┐
│  Host System (macOS)                             │
│  ├── Homebrew (openclaw-cli)                     │
│  ├── LaunchAgents (watchdog daemon)              │
│  ├── Docker (containerized watchdog)             │
│  └── ~/.openclaw/ (runtime state, logs, memory)  │
└─────────────────────────────────────────────────┘
```

## Directory Layout

```
openclaw-sysadmin-agent/
├── pyproject.toml                 # Poetry project config — entry points, deps, linting
├── tools/                         # Python package (installed via pip/poetry)
│   ├── __init__.py
│   ├── archive.py                 # Memory file archiver (oc-archive)
│   ├── security_audit.py          # Sensitive data checker (oc-security-audit)
│   ├── iamq.py                    # Inter-Agent Message Queue client (oc-iamq)
│   └── pipeline_runner/           # CI/CD pipeline runner (oc-pipeline)
│       ├── __init__.py
│       ├── __main__.py            # python -m tools.pipeline_runner
│       ├── cli.py                 # CLI entry point and pipeline registry
│       ├── runner.py              # Pipeline orchestration and result reporting
│       └── pipelines/             # Individual pipeline implementations
│           ├── __init__.py
│           ├── security.py        # Sensitive data scan (code + history)
│           ├── validate.py        # Lint, agent files, Docker build
│           ├── docs.py            # Internal link check, TODO markers
│           └── iamq.py            # IAMQ health and registration check
├── scripts/                       # Shell scripts (macOS-native tasks)
│   ├── watchdog.sh                # Host-native gateway watchdog
│   ├── close-tabs.sh              # Browser tab cleanup (Keyboard Maestro)
│   ├── security-audit.sh          # Legacy bash audit (still works)
│   ├── install-watchdog.sh        # LaunchAgent installer/uninstaller
│   └── templates/
│       └── watchdog.plist.template  # LaunchAgent template
├── watchdog/                      # Docker-based gateway monitor
│   ├── Dockerfile                 # Containerized watchdog (Alpine 3.20)
│   ├── docker-compose.yml         # Docker Compose config
│   └── watchdog.sh                # Container watchdog script
├── CLAUDE.md                      # Instructions for dev agents (Claude Code, etc.)
├── AGENTS.md                      # Agent behavior contract (read by OpenClaw agent)
├── SOUL.md                        # Agent identity, tone, boundaries
├── IDENTITY.md                    # Agent name, emoji, avatar
├── USER.md                        # Info about the human being served
├── PROTOCOL.md                    # System maintenance runbook
├── HEARTBEAT.md                   # Periodic heartbeat task queue
├── TOOLS.md                       # Environment-specific tool notes
├── .env                           # Local secrets (gitignored)
├── .env.example                   # Template for .env
├── spec/
│   ├── ARCHITECTURE.md            # This file
│   ├── PIPELINES.md               # GitHub Actions CI/CD documentation
│   ├── TROUBLESHOOTING.md         # Common issues and fixes
│   ├── TESTING.md                 # How to test the setup
│   └── LEARNINGS.md               # Agent-maintained lessons learned
├── .github/workflows/             # GitHub Actions pipelines
│   ├── security-audit.yml         # Sensitive data scan
│   ├── validate.yml               # Lint, agent files, Docker build
│   └── docs.yml                   # Internal link check
├── logs/                          # Daily maintenance logs (gitignored)
└── archive/                       # Archived memory files (gitignored)
```

## Two Audiences

This repo serves **two distinct audiences**:

### 1. The OpenClaw Agent (runtime)
Files read at runtime by the sysadmin agent during its sessions:
- `AGENTS.md` — behavior contract, session startup, memory system
- `SOUL.md` — identity, tone, boundaries
- `IDENTITY.md` — name, emoji, avatar
- `USER.md` — human profile
- `PROTOCOL.md` — maintenance tasks and scheduling
- `HEARTBEAT.md` — periodic task queue
- `TOOLS.md` — environment-specific notes
- `spec/LEARNINGS.md` — accumulated wisdom from past issues

### 2. Dev Agents / Contributors (development)
Files read by Claude Code or human contributors improving the workspace:
- `CLAUDE.md` — development instructions, progressive disclosure
- `spec/ARCHITECTURE.md` — this file
- `spec/TROUBLESHOOTING.md` — known issues
- `spec/TESTING.md` — validation procedures
- `README.md` — public onboarding

## Python Tooling

The `tools/` package is managed via Poetry (`pyproject.toml`):

| Entry Point | Module | Purpose |
|-------------|--------|---------|
| `oc-pipeline` | `tools.pipeline_runner.cli` | Run CI/CD pipelines locally |
| `oc-archive` | `tools.archive` | Archive old memory files |
| `oc-security-audit` | `tools.security_audit` | Standalone security audit |
| `oc-iamq` | `tools.iamq` | Inter-Agent Message Queue client |

Install: `pip install .` (minimal) or `poetry install` (dev environment with ruff + pytest).

The pipeline runner is also the backbone of GitHub Actions — each workflow calls `python -m tools.pipeline_runner <pipeline>`.

## Scheduling

The agent uses two scheduling mechanisms (see `AGENTS.md` → Heartbeats):

| Mechanism | When to use | Examples |
|-----------|-------------|---------|
| **Heartbeat** | Batched checks, approximate timing | Inbox, calendar, memory review |
| **Cron** | Exact timing, isolated tasks | Archive maintenance, one-shot reminders |

**Scheduled tasks:**
- **Watchdog** — Continuous (launchd or Docker), checks every 60s (host) or 5m (Docker)
- **Archive** — Weekly via `oc-archive` / `python -m tools.archive` (agent runs during maintenance)
- **Security audit** — Daily via `openclaw security audit --deep` + `oc-security-audit`

## Inter-Agent Message Queue (IAMQ)

The sysadmin agent communicates with other OpenClaw agents via the IAMQ service (Elixir/OTP), hosted at `~/Ws/Openclaw/openclaw-inter-agent-message-queue/`.

- **Agent ID:** `sysadmin_agent`
- **HTTP API:** `http://127.0.0.1:18790`
- **WebSocket:** `ws://127.0.0.1:18793`
- **Client:** `tools/iamq.py` (`oc-iamq` / `python -m tools.iamq`)
- **Health pipeline:** `python -m tools.pipeline_runner iamq`

The agent registers on session startup, sends heartbeats during each heartbeat cycle, and checks its inbox for messages from peer agents. See `TOOLS.md` for the full list of peer agents.

## Key Design Decisions

1. **Poetry + pyproject.toml** — Single source of truth for project metadata, dependencies, entry points, and linting config. CI installs via `pip install .` for speed.
2. **tools/ as a Python package** — Pipeline runner, archive, security audit, and IAMQ client are proper Python modules with CLI entry points. Testable, importable, type-checkable.
3. **Shell scripts for macOS-native tasks** — Watchdog daemon, launchd installer, and tab cleanup remain as bash because they interact directly with macOS system services.
4. **Environment variables over hardcoded paths** — All local paths and secrets live in `.env`, never in committed code.
5. **Progressive disclosure** — Both CLAUDE.md and AGENTS.md link to spec/ for deep dives, keeping top-level files scannable.
6. **Gitignored runtime data** — `logs/`, `archive/`, `.openclaw/`, and `.env` never hit the repo.
7. **CI/CD via pipeline_runner** — GitHub Actions call the same Python pipelines that run locally. See `spec/PIPELINES.md`.
8. **IAMQ integration** — The agent is a first-class participant in the inter-agent message queue, enabling discovery and communication with all peer agents.
