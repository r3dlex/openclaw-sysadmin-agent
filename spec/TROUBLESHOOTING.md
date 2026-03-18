# Troubleshooting

> Common issues and how to resolve them. The agent should consult this before escalating.

## Gateway Issues

### Gateway not starting
```bash
# Check status
openclaw gateway status

# Try restart
openclaw gateway stop && sleep 2 && openclaw gateway start

# If stuck, run doctor
openclaw doctor --fix

# Nuclear option: reinstall gateway
openclaw gateway install
```

### Gateway healthy but not responding to messages
- Check channel connections: `openclaw gateway status` (look for channel status)
- Verify WhatsApp QR code hasn't expired
- Check browser relay extension is installed

### Port conflict on 18789
```bash
lsof -i :18789
# Kill the conflicting process or change OPENCLAW_PORT in .env
```

## Watchdog Issues

### Watchdog not starting (launchd)
```bash
# Check if loaded
launchctl list | grep openclaw

# Reload
launchctl unload ~/Library/LaunchAgents/com.openclaw.watchdog.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.watchdog.plist

# Check logs
tail -50 ~/.openclaw/logs/watchdog.log
```

### Watchdog not starting (Docker)
```bash
cd watchdog/
docker compose logs -f
docker compose restart
```

### Lock file stale
If the watchdog won't start due to a stale lock file:
```bash
rm ~/.openclaw/.watchdog.lock
```
The watchdog checks if the PID in the lock file is still alive, but after a crash this can get stuck.

## Brew Update Issues

### Stale Homebrew lock
```bash
rm -f /opt/homebrew/var/homebrew/locks/*.lock
brew update
```

### OpenClaw CLI not found after upgrade
```bash
which openclaw
brew link --overwrite openclaw-cli
```

## Memory / Archive Issues

### Memory directory missing
```bash
mkdir -p ~/.openclaw/workspace/memory
```

### Archive script fails
- Check that `MEMORY_DIR` and `ARCHIVE_DIR` in `.env` are correct
- Ensure the archive directory exists or the script can create it

## Security

### Running a security audit
```bash
openclaw security audit --deep
```

### Token expiry
- Check `agent_mail_ops/artifacts/` for token files
- Attempt refresh; if failed, escalate to the user

## Logs

All logs are in `~/.openclaw/logs/`. Daily maintenance logs are in the workspace `logs/` directory (gitignored).

```bash
# Watchdog log
tail -f ~/.openclaw/logs/watchdog.log

# Recent maintenance log
ls -t logs/ | head -1 | xargs cat
```
