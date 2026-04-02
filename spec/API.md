# API — openclaw-sysadmin-agent

## Overview

The Sysadmin agent does not expose an HTTP server. All cross-agent interaction
uses IAMQ. Operators can also invoke tools directly via the Python CLI or
shell scripts.

---

## IAMQ Message Interface

### Incoming messages accepted by `sysadmin_agent`

| Subject | Purpose | Body fields |
|---------|---------|-------------|
| `sysadmin.health_check` | Run a gateway health check and return result | — |
| `sysadmin.security_audit` | Run the security audit (report-only) | — |
| `sysadmin.system_info` | Return system metrics (CPU, RAM, disk, uptime) | — |
| `sysadmin.brew_upgrade` | Run `brew upgrade --dry-run` and return pending upgrades | — |
| `sysadmin.archive` | Run the memory archive job | — |
| `sysadmin.logs` | Return recent log entries | `lines?: number`, `level?: "info"\|"warn"\|"error"` |
| `status` | Return agent health and last audit/check timestamps | — |

#### Example: request a health check

```json
{
  "from": "agent_claude",
  "to": "sysadmin_agent",
  "type": "request",
  "priority": "HIGH",
  "subject": "sysadmin.health_check",
  "body": {}
}
```

#### Example response

```json
{
  "from": "sysadmin_agent",
  "to": "agent_claude",
  "type": "response",
  "priority": "HIGH",
  "subject": "sysadmin.health_check.result",
  "body": {
    "gateway_status": "healthy",
    "uptime_seconds": 86400,
    "cpu_percent": 12.3,
    "ram_used_gb": 6.1,
    "disk_free_gb": 234.5,
    "timestamp": "2026-04-02T03:01:00Z"
  }
}
```

#### Example: security audit result

```json
{
  "from": "sysadmin_agent",
  "to": "agent_claude",
  "type": "response",
  "subject": "sysadmin.security_audit.result",
  "body": {
    "status": "clean",
    "findings": [],
    "scanned_repos": 12,
    "duration_seconds": 45
  }
}
```

---

## CLI / Python Tools

```bash
# Security audit
python -m tools.security_audit

# Run all pipelines (validate, security, docs, iamq)
python -m tools.pipeline_runner

# Specific pipeline
python -m tools.pipeline_runner security
python -m tools.pipeline_runner validate

# IAMQ tools
python -m tools.iamq agents       # See who's online
python -m tools.iamq inbox        # Check inbox
python -m tools.iamq send <to> "Subject" "Body"

# Memory archive
python -m tools.archive
```

---

## Watchdog (Independent)

The watchdog daemon runs independently of the agent and does not communicate
via IAMQ. It monitors the gateway process and restarts it if down:

- **Host mode**: `scripts/watchdog.sh` via `launchd` (60-second interval)
- **Docker mode**: `watchdog/watchdog.sh` via `docker compose` (5-minute interval)

The agent monitors watchdog status via `sysadmin.health_check` but does not
control the watchdog directly.

---

**Related:** `spec/COMMUNICATION.md`, `spec/CRON.md`, `spec/ARCHITECTURE.md`
