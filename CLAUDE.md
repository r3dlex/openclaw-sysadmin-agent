# CLAUDE.md — Development Guide

> Instructions for Claude Code and other dev agents working on this repository.
> This file is for **you** (the dev agent), not for the OpenClaw sysadmin agent.

## What This Repo Is

An [OpenClaw](https://docs.openclaw.ai/) agent workspace where an AI agent acts as a **system administrator** for a macOS host. The agent monitors gateway health, runs maintenance tasks, manages memory, and responds to heartbeats.

## Two Audiences — Don't Mix Them

| Audience | Reads | Purpose |
|----------|-------|---------|
| **OpenClaw agent** (runtime) | `AGENTS.md`, `SOUL.md`, `USER.md`, `PROTOCOL.md`, `HEARTBEAT.md`, `TOOLS.md`, `IDENTITY.md`, `spec/LEARNINGS.md` | Behavior at runtime |
| **Dev agents** (you) | `CLAUDE.md`, `spec/ARCHITECTURE.md`, `spec/TROUBLESHOOTING.md`, `spec/TESTING.md`, `README.md` | Improving the workspace |

When editing agent-facing files, remember: the OpenClaw agent is **autonomous** — it reads these files to decide what to do. It should be fully capable of operating without human intervention, while remaining entitled to make its own decisions.

## Key Rules

1. **No sensitive data in git.** Paths, phone numbers, tokens, credentials — all go in `.env` (gitignored). Use `${HOME}` or env vars in scripts.
2. **Python-first tooling.** Core tools live in `tools/` as a Poetry-managed Python package. Shell scripts in `scripts/` are for macOS-native tasks only (watchdog daemon, launchd installer, tab cleanup).
3. **Progressive disclosure.** Keep top-level files scannable. Link to `spec/` for deep dives.
4. **Zero-install for runtime.** Shell scripts run natively on macOS. Python tools install via `pip install .` or `poetry install` — stdlib only at runtime, optional `python-dotenv`.

## Directory Layout

```
CLAUDE.md              ← You are here
pyproject.toml         ← Poetry project config (entry points, deps, linting)
tools/                 ← Python package (pipeline runner, archive, security audit, IAMQ)
scripts/               ← Shell scripts (watchdog, launchd installer, tab cleanup)
watchdog/              ← Docker-based gateway monitor
spec/                  ← Architecture, troubleshooting, testing, learnings
AGENTS.md              ← Agent behavior contract
SOUL.md / USER.md      ← Agent identity & user profile
PROTOCOL.md            ← Maintenance runbook
HEARTBEAT.md           ← Periodic task queue
TOOLS.md / IDENTITY.md ← Agent environment notes
.env.example           ← Template for local config
```

See `spec/ARCHITECTURE.md` for the full layout and design decisions.

## Common Tasks

### Running pipelines locally
```bash
# All pipelines
python -m tools.pipeline_runner

# Specific pipeline
python -m tools.pipeline_runner security
python -m tools.pipeline_runner validate
python -m tools.pipeline_runner docs
python -m tools.pipeline_runner iamq

# List available pipelines
python -m tools.pipeline_runner --list
```

### Running the security audit (standalone)
```bash
python -m tools.security_audit
# OR (legacy bash version, still works)
bash scripts/security-audit.sh
```

### Adding a new pipeline
1. Create `tools/pipeline_runner/pipelines/your_pipeline.py` with a `run()` function returning `PipelineResult`
2. Register it in `tools/pipeline_runner/cli.py` → `PIPELINES` dict
3. Document in `spec/PIPELINES.md`

### Adding a new Python tool
1. Create in `tools/` as a module with a `main()` function
2. Add a script entry point in `pyproject.toml` → `[tool.poetry.scripts]`
3. Reference from `PROTOCOL.md` so the agent knows about it

### Adding a shell script
1. Create in `scripts/` with `#!/usr/bin/env bash` and `set -euo pipefail`
2. Source `.env`: `source "$REPO_ROOT/.env"`
3. Use env vars for all paths
4. Reference from `PROTOCOL.md` so the agent knows about it

### IAMQ (inter-agent messaging)
```bash
python -m tools.iamq agents       # See who's online
python -m tools.iamq inbox        # Check inbox
python -m tools.iamq send <to> "Subject" "Body"
```

### Modifying agent behavior
Edit `AGENTS.md` (behavior contract) or `PROTOCOL.md` (task list). The agent reads these at session start.

### Installing the watchdog daemon
```bash
bash scripts/install-watchdog.sh          # Install via launchd
# OR
cd watchdog/ && docker compose up -d      # Install via Docker
```

## Before Committing

1. Run `python -m tools.pipeline_runner` — all pipelines must pass
2. Grep for `/Users/` in tracked files — should only appear in templates with `__HOME__` placeholders
3. Verify `.env` is gitignored: `git check-ignore .env`

GitHub Actions will run the same pipelines automatically on push/PR. See `spec/PIPELINES.md`.

## Spec (Deep Dives)

- `spec/ARCHITECTURE.md` — workspace design, directory layout, two-audience model
- `spec/PIPELINES.md` — GitHub Actions CI/CD pipelines
- `spec/TROUBLESHOOTING.md` — known issues and step-by-step fixes
- `spec/TESTING.md` — validation procedures and health checks
- `spec/LEARNINGS.md` — operational wisdom (maintained by the sysadmin agent)
