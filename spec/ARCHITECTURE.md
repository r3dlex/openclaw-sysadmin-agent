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
│  ├── scripts/       → Automation scripts         │
│  ├── watchdog/      → Gateway health monitor     │
│  └── spec/          → Architecture docs          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
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
├── CLAUDE.md                  # Instructions for dev agents (Claude Code, etc.)
├── AGENTS.md                  # Agent behavior contract (read by OpenClaw agent)
├── SOUL.md                    # Agent identity, tone, boundaries
├── IDENTITY.md                # Agent name, emoji, avatar
├── USER.md                    # Info about the human being served
├── PROTOCOL.md                # System maintenance runbook
├── HEARTBEAT.md               # Periodic heartbeat task queue
├── TOOLS.md                   # Environment-specific tool notes
├── .env                       # Local secrets (gitignored)
├── .env.example               # Template for .env
├── scripts/
│   ├── watchdog.sh            # Host-native gateway watchdog
│   ├── archive.py             # Memory file archiver (weekly)
│   ├── close-tabs.sh          # Browser tab cleanup
│   ├── security-audit.sh      # Sensitive data + openclaw audit
│   ├── install-watchdog.sh    # LaunchAgent installer/uninstaller
│   └── templates/
│       └── watchdog.plist.template  # LaunchAgent template
├── watchdog/
│   ├── Dockerfile             # Containerized watchdog (Alpine 3.20)
│   ├── docker-compose.yml     # Docker Compose config
│   └── watchdog.sh            # Container watchdog script
├── spec/
│   ├── ARCHITECTURE.md        # This file
│   ├── TROUBLESHOOTING.md     # Common issues and fixes
│   ├── TESTING.md             # How to test the setup
│   └── LEARNINGS.md           # Agent-maintained lessons learned
├── logs/                      # Daily maintenance logs (gitignored)
└── archive/                   # Archived memory files (gitignored)
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

## Scheduling

The agent uses two scheduling mechanisms (see `AGENTS.md` → Heartbeats):

| Mechanism | When to use | Examples |
|-----------|-------------|---------|
| **Heartbeat** | Batched checks, approximate timing | Inbox, calendar, memory review |
| **Cron** | Exact timing, isolated tasks | Archive maintenance, one-shot reminders |

**Scheduled tasks:**
- **Watchdog** — Continuous (launchd or Docker), checks every 60s (host) or 5m (Docker)
- **Archive** — Weekly via `python3 scripts/archive.py` (agent runs during maintenance)
- **Security audit** — Daily via `openclaw security audit --deep` + `bash scripts/security-audit.sh`

## Key Design Decisions

1. **Environment variables over hardcoded paths** — All local paths and secrets live in `.env`, never in committed code.
2. **Progressive disclosure** — Both CLAUDE.md and AGENTS.md link to spec/ for deep dives, keeping top-level files scannable.
3. **Zero-install scripts** — The watchdog can run natively via launchd OR containerized via Docker. Scripts source `.env` for configuration.
4. **Gitignored runtime data** — `logs/`, `archive/`, `.openclaw/`, and `.env` never hit the repo.
5. **Security audit built-in** — The agent periodically runs `openclaw security audit --deep` as part of its maintenance protocol.
6. **Validation** — Run `bash scripts/security-audit.sh` before commits. See `spec/TESTING.md` for full procedures.
