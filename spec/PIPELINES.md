# Pipelines

> GitHub Actions CI/CD pipelines for this repository.
> Referenced from: `CLAUDE.md`, `spec/ARCHITECTURE.md`, `spec/TESTING.md`

## Overview

All pipelines run on `push` to `main` and on pull requests. They require no secrets or external services — everything runs in the GitHub Actions runner.

```
Push / PR to main
  ├── Security Audit        → Scan for sensitive data in code + git history
  ├── Validate
  │   ├── Lint Scripts      → shellcheck + py_compile + ruff
  │   ├── Agent Files       → Required .md files exist and are non-empty
  │   └── Docker Build      → Watchdog container builds and starts
  └── Docs                  → Internal link check + TODO marker scan
```

## Pipelines

### 1. Security Audit (`.github/workflows/security-audit.yml`)

**Trigger:** Every push and PR to `main`

| Check | What it does | Fails on |
|-------|-------------|----------|
| Hardcoded paths | Scans tracked files for `/Users/` | Real user paths in code |
| Phone numbers | Scans for `+` followed by 10+ digits | Phone numbers outside `.env.example` |
| Secret patterns | Scans for `api_key=`, `password=`, etc. | Credentials in code |
| Gitignore verify | Confirms `.env`, `logs/`, `archive/`, `.openclaw/` are ignored | Missing gitignore rules |
| History scan | Scans full git history for leaked secrets | Sensitive data in past commits |

This is the **most critical pipeline**. If it fails, do not merge.

### 2. Validate (`.github/workflows/validate.yml`)

**Trigger:** Every push and PR to `main`

| Job | What it does |
|-----|-------------|
| **Lint Shell Scripts** | Runs `shellcheck` on all `scripts/*.sh` (warnings non-blocking) |
| **Lint Python** | Runs `py_compile` + `ruff` on `scripts/archive.py` |
| **Validate Agent Files** | Checks that all required agent `.md` files exist and are non-empty |
| **Docker Build** | Builds the watchdog container and verifies it starts |

### 3. Docs (`.github/workflows/docs.yml`)

**Trigger:** Push/PR to `main` when `.md` files change

| Check | What it does |
|-------|-------------|
| Internal links | Verifies `[text](path)` links in markdown resolve to real files |
| TODO markers | Warns on stale `TODO`/`FIXME`/`HACK` markers in docs |

## Running Locally

All pipeline checks can be run locally before pushing:

```bash
# Security audit (mirrors the pipeline)
bash scripts/security-audit.sh

# Shell lint
shellcheck scripts/*.sh

# Python lint
python3 -m py_compile scripts/archive.py

# Docker build
cd watchdog/ && docker compose build

# Agent file validation
for f in AGENTS.md SOUL.md IDENTITY.md USER.md PROTOCOL.md HEARTBEAT.md TOOLS.md; do
  test -s "$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

See `spec/TESTING.md` for the full local validation guide.

## Adding a New Pipeline

1. Create `.github/workflows/<name>.yml`
2. Document it in this file
3. Reference from `CLAUDE.md` and/or `spec/TESTING.md` if relevant
4. Ensure it requires no secrets (this is a public repo)

## Design Principles

- **No secrets required** — Pipelines work on public forks without any GitHub Secrets
- **Fast feedback** — Jobs run in parallel where possible
- **Non-destructive** — Pipelines only read and validate; they never modify the repo
- **Mirror local tools** — Every CI check has a local equivalent in `scripts/`
