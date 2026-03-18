#!/usr/bin/env python3
"""
Archive old memory files.

Moves memory .md files older than ARCHIVE_DAYS_THRESHOLD (default: 30 days)
from MEMORY_DIR to ARCHIVE_DIR.

Configuration via .env file in the repo root, or environment variables:
    MEMORY_DIR              Path to memory directory
    ARCHIVE_DIR             Path to archive directory
    ARCHIVE_DAYS_THRESHOLD  Number of days before archiving (default: 30)

See: specs/ARCHITECTURE.md for directory layout
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Load .env if python-dotenv is available, otherwise rely on environment
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.expanduser("~/.openclaw/workspace/memory"))
ARCHIVE_DIR = os.environ.get("ARCHIVE_DIR", os.path.expanduser("~/.openclaw/workspace/system_maintenance/archive"))
DAYS_THRESHOLD = int(os.environ.get("ARCHIVE_DAYS_THRESHOLD", "30"))


def main() -> None:
    print(f"Memory Archive Maintenance — {datetime.now().isoformat()}")
    print(f"  Source:    {MEMORY_DIR}")
    print(f"  Archive:   {ARCHIVE_DIR}")
    print(f"  Threshold: {DAYS_THRESHOLD} days")

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    if not os.path.isdir(MEMORY_DIR):
        print(f"Memory directory not found: {MEMORY_DIR}")
        return

    cutoff = datetime.now() - timedelta(days=DAYS_THRESHOLD)
    archived = 0

    for filename in sorted(os.listdir(MEMORY_DIR)):
        if not filename.endswith(".md"):
            continue

        filepath = os.path.join(MEMORY_DIR, filename)
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

        if mtime < cutoff:
            dest = os.path.join(ARCHIVE_DIR, filename)
            shutil.move(filepath, dest)
            print(f"  Archived: {filename}")
            archived += 1

    print(f"\nDone. Archived {archived} file(s).")


if __name__ == "__main__":
    main()
