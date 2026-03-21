"""Archive old memory files.

Moves memory .md files older than ARCHIVE_DAYS_THRESHOLD (default: 30 days)
from MEMORY_DIR to ARCHIVE_DIR.

Configuration via .env file in the repo root, or environment variables:
    MEMORY_DIR              Path to memory directory
    ARCHIVE_DIR             Path to archive directory
    ARCHIVE_DAYS_THRESHOLD  Number of days before archiving (default: 30)

Usage:
    oc-archive                          # Via Poetry script entry point
    python -m tools.archive             # Direct module invocation

See: spec/ARCHITECTURE.md for directory layout
"""

from __future__ import annotations

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

MEMORY_DIR = Path(
    os.environ.get("MEMORY_DIR", os.path.expanduser("~/.openclaw/workspace/memory"))
)
ARCHIVE_DIR = Path(
    os.environ.get(
        "ARCHIVE_DIR", os.path.expanduser("~/.openclaw/workspace/system_maintenance/archive")
    )
)
DAYS_THRESHOLD = int(os.environ.get("ARCHIVE_DAYS_THRESHOLD", "30"))


def main() -> None:
    """Archive memory files older than the configured threshold."""
    print(f"Memory Archive Maintenance — {datetime.now().isoformat()}")
    print(f"  Source:    {MEMORY_DIR}")
    print(f"  Archive:   {ARCHIVE_DIR}")
    print(f"  Threshold: {DAYS_THRESHOLD} days")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_DIR.is_dir():
        print(f"Memory directory not found: {MEMORY_DIR}")
        return

    cutoff = datetime.now() - timedelta(days=DAYS_THRESHOLD)
    archived = 0

    for filepath in sorted(MEMORY_DIR.iterdir()):
        if filepath.suffix != ".md":
            continue

        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        if mtime < cutoff:
            dest = ARCHIVE_DIR / filepath.name
            shutil.move(str(filepath), str(dest))
            print(f"  Archived: {filepath.name}")
            archived += 1

    print(f"\nDone. Archived {archived} file(s).")


if __name__ == "__main__":
    main()
