# CLAUDE.md — Development Guide

> Instructions for Claude Code and other dev agents working on this repository.
> This file is for **you** (the dev agent), not for the OpenClaw sysadmin agent.

## What This Repo Is

An [OpenClaw](https://docs.openclaw.ai/) agent workspace where an AI agent acts as a **system administrator** for a macOS host. The agent monitors gateway health, runs maintenance tasks, manages memory, and responds to heartbeats.

## Two Audiences — Don't Mix Them

| Audience | Reads | Purpose |
|----------|-------|---------|
| **OpenClaw agent** (runtime) | `AGENTS.md`, `SOUL.md`, `USER.md`, `PROTOCOL.md`, `HEARTBEAT.md`, `TOOLS.md`, `IDENTITY.md`, `specs/LEARNINGS.md` | Behavior at runtime |
| **Dev agents** (you) | `CLAUDE.md`, `specs/ARCHITECTURE.md`, `specs/TROUBLESHOOTING.md`, `specs/TESTING.md`, `README.md` | Improving the workspace |

When editing agent-facing files, remember: the OpenClaw agent is **autonomous** — it reads these files to decide what to do. It should be fully capable of operating without human intervention, while remaining entitled to make its own decisions.

## Key Rules

1. **No sensitive data in git.** Paths, phone numbers, tokens, credentials — all go in `.env` (gitignored). Use `${HOME}` or env vars in scripts.
2. **Scripts source `.env`.** All scripts in `scripts/` load `../.env` for configuration. No hardcoded paths.
3. **Progressive disclosure.** Keep top-level files scannable. Link to `specs/` for deep dives.
4. **Zero-install.** Scripts run natively on macOS or via Docker (`watchdog/`). No pip install required (archive.py uses stdlib, optional dotenv).

## Directory Layout

```
CLAUDE.md              ← You are here
AGENTS.md              ← Agent behavior contract
SOUL.md / USER.md      ← Agent identity & user profile
PROTOCOL.md            ← Maintenance runbook
HEARTBEAT.md           ← Periodic task queue
TOOLS.md / IDENTITY.md ← Agent environment notes
scripts/               ← Automation (watchdog, archive, tabs, security)
watchdog/              ← Docker-based gateway monitor
specs/                 ← Architecture, troubleshooting, testing, learnings
.env.example           ← Template for local config
```

See `specs/ARCHITECTURE.md` for the full layout and design decisions.

## Common Tasks

### Adding a new maintenance script
1. Create in `scripts/` with `#!/usr/bin/env bash` and `set -euo pipefail`
2. Source `.env`: `source "$REPO_ROOT/.env"`
3. Use env vars for all paths
4. Reference from `PROTOCOL.md` so the agent knows about it
5. Make executable: `chmod +x scripts/your-script.sh`

### Modifying agent behavior
Edit `AGENTS.md` (behavior contract) or `PROTOCOL.md` (task list). The agent reads these at session start.

### Adding a troubleshooting entry
Add to `specs/TROUBLESHOOTING.md`. The agent consults this before escalating.

### Running the security audit
```bash
bash scripts/security-audit.sh
```

### Installing the watchdog daemon
```bash
bash scripts/install-watchdog.sh          # Install via launchd
# OR
cd watchdog/ && docker compose up -d      # Install via Docker
```

## Before Committing

1. Run `bash scripts/security-audit.sh` — must pass with 0 issues
2. Grep for `/Users/` in tracked files — should only appear in templates with `__HOME__` placeholders
3. Verify `.env` is gitignored: `git check-ignore .env`
4. Verify `logs/` and `archive/` are gitignored

## Specs (Deep Dives)

- `specs/ARCHITECTURE.md` — workspace design, directory layout, two-audience model
- `specs/TROUBLESHOOTING.md` — known issues and step-by-step fixes
- `specs/TESTING.md` — validation procedures and health checks
- `specs/LEARNINGS.md` — operational wisdom (maintained by the sysadmin agent)
