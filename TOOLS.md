# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Inter-Agent Message Queue (IAMQ)

The IAMQ service enables communication with other OpenClaw agents in this environment.

**Your agent ID:** `sysadmin_agent`
**Service:** `http://127.0.0.1:18790` (HTTP) / `ws://127.0.0.1:18793` (WebSocket)

### Quick Reference

```bash
# Check your inbox
python -m tools.iamq inbox --unread

# Send a message to another agent
python -m tools.iamq send mail_agent "Subject" "Body text"

# Broadcast to all agents
python -m tools.iamq broadcast "Subject" "Body text"

# Send heartbeat (keeps you registered)
python -m tools.iamq heartbeat

# See who's online
python -m tools.iamq agents

# Mark a message as read
python -m tools.iamq ack <message-uuid>
```

### Known Peer Agents

| Agent ID | Role |
|----------|------|
| `main` | Primary assistant |
| `mail_agent` | Email operations |
| `librarian_agent` | Research and knowledge |
| `journalist_agent` | News and writing |
| `instagram_agent` | Social media |
| `gitrepo_agent` | Git repository management |
| `archivist_agent` | Archival and long-term storage |
| `health_fitness` | Health and fitness tracking |
| `workday_agent` | Work scheduling |
| `mq_agent` | Message queue management |

### Message Protocol

Messages use this format:
- **priority:** `URGENT`, `HIGH`, `NORMAL`, `LOW`
- **type:** `request`, `response`, `info`, `error`
- **status:** `unread` → `read` → `acted` → `archived`

For full protocol details, see the IAMQ repo at `~/Ws/Openclaw/openclaw-inter-agent-message-queue/spec/PROTOCOL.md`.

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
