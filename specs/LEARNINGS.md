# Learnings

> Accumulated wisdom from the sysadmin agent's operational experience.
> The agent updates this file as it encounters and resolves issues.
> See also: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for step-by-step fixes.

## Gateway

- After `brew upgrade`, the gateway often needs a manual restart. The watchdog handles this automatically, but if the watchdog itself was interrupted during the upgrade, you may need to restart it first.
- Gateway health checks can false-positive during the 3-5 AM backup window. The watchdog skips checks during this period intentionally.
- `openclaw doctor --fix` resolves most gateway issues that a simple restart doesn't.

## Homebrew

- Stale lock files (`/opt/homebrew/var/homebrew/locks/*.lock`) are the #1 cause of failed `brew update`. Remove them before retrying.
- `mas upgrade` (Mac App Store) requires sudo/GUI context and will fail in headless agent sessions. Skip it gracefully.

## Memory Management

- Memory files older than 30 days are archived automatically. If the agent references something old, check the archive.
- `MEMORY.md` is for curated long-term memory. Daily files are raw logs. Don't mix them.

## Security

- Always run `openclaw security audit --deep` after configuration changes.
- Never log or commit tokens, phone numbers, or credentials.
- The `.env` file must remain gitignored at all times.

---

*This file is maintained by the sysadmin agent. Last reviewed: 2026-03-18*
