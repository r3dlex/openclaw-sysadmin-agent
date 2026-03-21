# System Maintenance Protocol

> The sysadmin agent's runbook. Read this at session start alongside `AGENTS.md`.
> For troubleshooting, see `spec/TROUBLESHOOTING.md`.

## Daily Tasks

### 1. OpenClaw Version Check
- Run `openclaw status` to check for updates
- If update available: `brew upgrade openclaw-cli` then `openclaw gateway restart`
- After upgrade, verify gateway health: `openclaw gateway status`

### 2. Gateway Health Check
- Verify gateway: `openclaw gateway status`
- If not running: `openclaw gateway start`
- If stuck: `openclaw gateway restart`
- See `spec/TROUBLESHOOTING.md` for escalation steps

### 3. Browser Relay Check
- Verify browser extension is installed: `openclaw browser status`
- If missing, reinstall via the OpenClaw Skills tab or `openclaw browser install`

### 4. Security Audit
- Run `openclaw security audit --deep`
- Also run `python -m tools.security_audit` to check for sensitive data in the repo
- Report any findings to the user

### 5. IAMQ Check
- Send heartbeat: `python -m tools.iamq heartbeat`
- Check inbox: `python -m tools.iamq inbox --unread`
- Process and respond to any messages from peer agents
- After gateway changes, broadcast to all agents: `python -m tools.iamq broadcast "Gateway status" "Details"`

## Weekly Tasks

### 1. Self-Maintenance
- Check installed version vs latest (`openclaw status`)
- If update available: upgrade, restart gateway, update Chrome extension
- **Config safeguard:** Before editing `openclaw.json`, create a timestamped backup

### 2. Workspace Backup
- Backup workspace to the configured backup drive (`BACKUP_DRIVE_PATH` in `.env`)
- Use rsync for efficient mirroring

### 3. Archive Old Memory Files
- Run: `python -m tools.archive`
- Archives memory files older than the configured threshold (default: 30 days)

### 4. Browser Relay Extension Check
- Verify browser extension is installed and working: `openclaw browser status`
- Reinstall if needed via Skills tab

### 5. Security Review
- Review `spec/LEARNINGS.md` for any security-relevant entries
- Verify `.env` is not tracked by git
- Check for any exposed credentials or tokens

## Watchdog

The gateway watchdog monitors health and auto-restarts after brew upgrades.

**Native (launchd):**
```bash
bash scripts/install-watchdog.sh
```

**Docker:**
```bash
cd watchdog/ && docker compose up -d
```

See `spec/TROUBLESHOOTING.md` → "Watchdog Issues" for common problems.

## Credentials

### Email/Calendar Token Monitoring
- Check token expiry in `agent_mail_ops/artifacts/`
- Report expired tokens to user
- Attempt refresh if possible

## Learnings

When you encounter a new issue or learn something:
1. Fix the immediate problem
2. Add the solution to `spec/TROUBLESHOOTING.md`
3. Add the lesson to `spec/LEARNINGS.md`

## Validation

After any maintenance run, verify the setup: see `spec/TESTING.md` for procedures.

---

Last updated: 2026-03-21
