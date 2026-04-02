# Cron

> Scheduled tasks and their cadences for the sysadmin agent.
> Referenced from: `AGENTS.md`, `HEARTBEAT.md`, `PROTOCOL.md`, `spec/ARCHITECTURE.md`

## Overview

The agent uses two scheduling mechanisms (see `spec/ARCHITECTURE.md` → Scheduling):

| Mechanism | Purpose | Examples |
|-----------|---------|---------|
| **Heartbeat** | Batched checks, approximate timing | IAMQ heartbeat, inbox poll |
| **Cron** | Exact timing, isolated tasks | Brew upgrade, security audit, archive |

## Task Schedule

### High-Frequency (heartbeat-driven)

| Task | Interval | Tool | Notes |
|------|----------|------|-------|
| IAMQ heartbeat | 60 seconds | `oc-iamq heartbeat` | Keeps agent registered; missed heartbeats expire after 5 minutes |
| Inbox poll | 30 seconds | `oc-iamq inbox --unread` | Process and act on unread messages |
| Gateway health check | 5 minutes | `openclaw gateway status` | Alert via IAMQ if unhealthy; watchdog handles restarts independently |

### Daily

| Task | Schedule | Tool | Notes |
|------|----------|------|-------|
| Brew upgrade check | 3:00 AM | `brew upgrade --dry-run` then `brew upgrade` | Dry-run first, report changes; one per day max (see `spec/SAFETY.md`) |
| Security audit | Once daily | `python -m tools.security_audit` | Report-only; max once per 6 hours (see `spec/SAFETY.md`) |

### Weekly

| Task | Schedule | Tool | Notes |
|------|----------|------|-------|
| Memory archive | Weekly | `python -m tools.archive` | Copy old memory files to archive; never delete originals |

## Watchdog (independent)

The watchdog runs outside the agent's heartbeat cycle:

| Mode | Interval | How |
|------|----------|-----|
| Host (launchd) | 60 seconds | `scripts/watchdog.sh` via LaunchAgent |
| Docker | 5 minutes | `watchdog/watchdog.sh` via `docker compose` |

The watchdog restarts the gateway autonomously. The agent monitors its status but does not control it directly.

## Timing Notes

- **3 AM brew upgrade** avoids conflicts with the gateway backup window (3-5 AM). The upgrade runs first; gateway health checks may false-positive during this period (see `spec/LEARNINGS.md`).
- **Inbox poll at 30s** is faster than heartbeat (60s) so messages are processed promptly.
- **Gateway health at 5m** complements the watchdog (60s host / 5m Docker) — the agent provides a second opinion, not a replacement.

## Adding a Scheduled Task

1. Decide: heartbeat-driven (approximate) or cron (exact)?
2. Add the task to `HEARTBEAT.md` (heartbeat) or `PROTOCOL.md` (cron)
3. Document it in this file with interval, tool, and safety notes
4. If it has safety constraints, add them to `spec/SAFETY.md`

---

_See `HEARTBEAT.md` for the heartbeat protocol and `spec/SAFETY.md` for rate limits._

## References

- [IAMQ Cron Subsystem](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/CRON.md) — how cron schedules are stored and fired
- [IAMQ API — Cron endpoints](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/API.md#cron-scheduling)
- [IamqSidecar.MqClient.register_cron/3](https://github.com/r3dlex/openclaw-inter-agent-message-queue/tree/main/sidecar) — Elixir sidecar helper
- [openclaw-main-agent](https://github.com/r3dlex/openclaw-main-agent) — orchestrates cron-triggered pipelines
