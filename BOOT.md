# BOOT.md — Startup Registration

On first session, register yourself with the Inter-Agent Message Queue:

```bash
curl -X POST http://127.0.0.1:18790/register \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "sysadmin_agent",
    "name": "Sentinel 🛡️",
    "emoji": "🛡️",
    "description": "System guardian — monitors gateway health, runs maintenance, security audits",
    "capabilities": ["gateway_health", "security_audit", "watchdog", "brew_upgrade", "memory_archive", "system_maintenance"]
  }'
```

Or via the Python tool:

```bash
python -m tools.iamq register
```

After registering, check your inbox for any waiting messages:

```bash
python -m tools.iamq inbox --unread
```

Then proceed with session startup as described in `AGENTS.md`.
