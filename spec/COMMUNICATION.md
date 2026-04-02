# Communication

> IAMQ messaging patterns for the sysadmin agent.
> Referenced from: `AGENTS.md`, `HEARTBEAT.md`, `TOOLS.md`, `spec/ARCHITECTURE.md`

## Identity

| Field | Value |
|-------|-------|
| **Agent ID** | `sysadmin_agent` |
| **Service** | `http://127.0.0.1:18790` (HTTP) / `ws://127.0.0.1:18793` (WebSocket) |
| **Client** | `tools/iamq.py` (`oc-iamq` / `python -m tools.iamq`) |

## Capabilities

The agent registers with these capabilities on session startup:

```
gateway_health, security_audit, watchdog, brew_upgrade, memory_archive, system_maintenance
```

Registration:
```bash
oc-iamq register --capabilities "gateway_health,security_audit,watchdog,brew_upgrade,memory_archive,system_maintenance"
```

## CLI Operations

All IAMQ interactions go through the `oc-iamq` CLI:

```bash
# Registration & presence
oc-iamq register            # Register with IAMQ (session startup)
oc-iamq heartbeat           # Keep registration alive (every heartbeat cycle)

# Inbox
oc-iamq inbox               # List all messages
oc-iamq inbox --unread      # Unread only

# Sending
oc-iamq send <agent> "Subject" "Body"                          # Direct message
oc-iamq send <agent> "Re: Subject" "Body" --type response --reply-to <msg-id>  # Reply
oc-iamq broadcast "Subject" "Body"                             # All agents

# Message lifecycle
oc-iamq ack <msg-id>        # Mark as read
oc-iamq acted <msg-id>      # Mark as acted
```

## Message Patterns

### Alerts (outbound)

Send alerts to `main` when something needs attention:

```bash
oc-iamq send main "Gateway down" "Health check failed 3 consecutive times. Restarting." --type error --priority URGENT
```

### Status Reports (outbound)

Broadcast infrastructure changes to all agents:

```bash
oc-iamq broadcast "Brew upgrade complete" "Updated 4 packages. Gateway restarted." --type info
```

### Roll-Call (inbound)

When another agent broadcasts a roll-call or status request, respond with current state:

```bash
oc-iamq send <requester> "Status: operational" "Gateway: up. Watchdog: running. Last audit: 2h ago." --type response --reply-to <msg-id>
oc-iamq acted <msg-id>
```

### Requests (inbound)

Handle requests within scope. If outside scope, redirect:

```bash
# Can handle: gateway status, security audit results, system health
# Cannot handle: email, git, social media → tell sender which agent to contact
```

## Peer Agents

| Agent | Relationship |
|-------|-------------|
| `main` | Receives alerts, escalations, urgent notifications |
| `broadcast` | Status announcements, infrastructure changes |
| `mq_agent` | Message queue management, IAMQ health |
| All others | Respond to roll-calls and status requests on demand |

## Session Lifecycle

1. **Startup** — Register with IAMQ, announce online status
2. **Heartbeat cycle** — Send heartbeat, poll inbox, process messages
3. **Event-driven** — Send alerts/broadcasts as issues arise
4. **Shutdown** — No explicit deregistration (IAMQ expires stale agents)

---

_See `HEARTBEAT.md` for the heartbeat protocol and `TOOLS.md` for the full peer agent list._

## References

- [IAMQ HTTP API](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/API.md)
- [IAMQ WebSocket Protocol](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/PROTOCOL.md)
- [IAMQ Cron Scheduling](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/CRON.md)
- [Sidecar Client](https://github.com/r3dlex/openclaw-inter-agent-message-queue/tree/main/sidecar)
- [openclaw-main-agent](https://github.com/r3dlex/openclaw-main-agent)
