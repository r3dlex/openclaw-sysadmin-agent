# Pipelines

> GitHub Actions CI/CD pipelines for this repository.
> Referenced from: `CLAUDE.md`, `spec/ARCHITECTURE.md`, `spec/TESTING.md`

## Overview

All pipelines run on `push` to `main` and on pull requests. They require no secrets or external services — everything runs in the GitHub Actions runner.

All pipelines are powered by `tools/pipeline_runner`, the same Python module used for local validation.

```
Push / PR to main
  ├── Security Audit        → python -m tools.pipeline_runner security
  ├── Validate
  │   ├── Pipeline          → python -m tools.pipeline_runner validate
  │   └── Docker Build      → watchdog container builds and starts
  └── Docs                  → python -m tools.pipeline_runner docs
```

## Pipelines

### 1. Security Audit (`.github/workflows/security-audit.yml`)

**Trigger:** Every push and PR to `main`
**Runner:** `python -m tools.pipeline_runner security`
**Module:** `tools/pipeline_runner/pipelines/security.py`

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
**Runner:** `python -m tools.pipeline_runner validate`
**Module:** `tools/pipeline_runner/pipelines/validate.py`

| Check | What it does |
|-------|-------------|
| **Shell lint** | Runs `shellcheck` on all `scripts/*.sh` (warnings non-blocking) |
| **Python lint** | Runs `py_compile` + `ruff` on `tools/**/*.py` |
| **Agent files** | Checks that all required agent `.md` files exist and are non-empty |
| **Spec files** | Checks that all required spec `.md` files exist and are non-empty |
| **Docker build** | Builds the watchdog container (separate job in CI) |

### 3. Docs (`.github/workflows/docs.yml`)

**Trigger:** Push/PR to `main` when `.md` files change
**Runner:** `python -m tools.pipeline_runner docs`
**Module:** `tools/pipeline_runner/pipelines/docs.py`

| Check | What it does |
|-------|-------------|
| Internal links | Verifies `[text](path)` links in markdown resolve to real files |
| TODO markers | Warns on stale `TODO`/`FIXME`/`HACK` markers in docs |

### 4. IAMQ Health (local only)

**Trigger:** Manual — `python -m tools.pipeline_runner iamq`
**Module:** `tools/pipeline_runner/pipelines/iamq.py`

| Check | What it does |
|-------|-------------|
| **IAMQ reachable** | Verifies IAMQ service is up at configured URL |
| **Agent registered** | Confirms `sysadmin_agent` is registered |
| **Unread messages** | Warns if there are unread messages in inbox |
| **Peer agents** | Reports which other agents are online |

This pipeline is **local-only** (not in CI) because it requires a running IAMQ service.

## Running Locally

All pipeline checks can be run locally:

```bash
# Run all pipelines at once
python -m tools.pipeline_runner

# Run a specific pipeline
python -m tools.pipeline_runner security
python -m tools.pipeline_runner validate
python -m tools.pipeline_runner docs
python -m tools.pipeline_runner iamq

# List available pipelines
python -m tools.pipeline_runner --list

# Standalone security audit (with openclaw CLI integration)
python -m tools.security_audit

# Legacy bash security audit (still works)
bash scripts/security-audit.sh
```

If using Poetry entry points:
```bash
poetry install
oc-pipeline                   # All pipelines
oc-pipeline security          # Specific pipeline
oc-security-audit             # Standalone security audit
```

See `spec/TESTING.md` for the full local validation guide.

## Adding a New Pipeline

1. Create `tools/pipeline_runner/pipelines/<name>.py` with a `run()` function returning `PipelineResult`
2. Register it in `tools/pipeline_runner/cli.py` → `PIPELINES` dict
3. Document it in this file
4. If it needs a dedicated GitHub Actions workflow, create `.github/workflows/<name>.yml`
5. Ensure it requires no secrets (this is a public repo)

## Design Principles

- **Python-first** — Pipelines are Python modules, not bash scripts. Testable, composable, type-safe.
- **No secrets required** — Pipelines work on public forks without any GitHub Secrets
- **Fast feedback** — Jobs run in parallel where possible
- **Non-destructive** — Pipelines only read and validate; they never modify the repo
- **Mirror local tools** — Every CI check has a local equivalent via `python -m tools.pipeline_runner`
