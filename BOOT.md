# BOOT.md — Startup Registration

On every session start, register with the Inter-Agent Message Queue:

```bash
curl -s -X POST http://127.0.0.1:18790/register \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "sysadmin_agent",
    "name": "Sentinel 🛡️",
    "emoji": "🛡️",
    "description": "System guardian — monitors gateway health, runs maintenance, security audits",
    "capabilities": ["gateway_health", "security_audit", "watchdog", "brew_upgrade", "memory_archive", "system_maintenance"],
    "workspace": "<this workspace's absolute path>"
  }'
```

Or via the Python tool (includes all metadata automatically):

```bash
python -m tools.iamq register
```

Then send a heartbeat and check inbox:

```bash
python -m tools.iamq heartbeat
python -m tools.iamq inbox --unread
```

Process any unread messages — reply via MQ (`POST /send` with `replyTo`), not Telegram. Mark handled messages as `acted`.

Then proceed with session startup as described in `AGENTS.md`.
