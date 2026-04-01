"""Security audit — scans for sensitive data in the repo and runs openclaw audit.

Combines repo-level sensitive data checks with the OpenClaw security audit CLI.
This is the Python equivalent of scripts/security-audit.sh.

Usage:
    oc-security-audit               # Via Poetry script entry point
    python -m tools.security_audit   # Direct module invocation
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

GITIGNORE_REQUIRED = [".env", "logs/", "archive/", ".openclaw/"]

EXCLUDE_GLOBS = [
    ":(exclude).gitignore",
    ":(exclude)scripts/security-audit.sh",
    ":(exclude)spec/TESTING.md",
    ":(exclude)spec/PIPELINES.md",
    ":(exclude).github/",
    ":(exclude)tools/pipeline_runner/",
    ":(exclude)tools/security_audit.py",
    # Test files intentionally contain sensitive-looking strings as test data
    ":(exclude)tests/",
]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True, text=True,
    )


def _check_hardcoded_paths() -> int:
    result = _git("grep", "-n", "/Users/", "--", *EXCLUDE_GLOBS)
    hits = [
        line for line in result.stdout.strip().splitlines()
        if line and not re.search(r"template|example|TEMPLATE|__HOME__|grep.*Users", line)
    ]
    if hits:
        print("WARNING: Found hardcoded /Users/ paths in tracked files")
        for h in hits:
            print(f"  {h}")
        return 1
    print("OK: No hardcoded user paths found")
    return 0


def _check_phone_numbers() -> int:
    result = _git(
        "grep", "-nE", r"\+[0-9]{10,}",
        "--", ":(exclude).env.example", ":(exclude).github/",
        ":(exclude)tools/pipeline_runner/", ":(exclude)tools/security_audit.py",
    )
    if result.stdout.strip():
        print("WARNING: Found possible phone numbers in tracked files")
        return 1
    print("OK: No phone numbers found")
    return 0


def _check_secrets_patterns() -> int:
    result = _git(
        "grep", "-nEi", r"(api_key|secret_key|password|token)\s*=",
        "--", "*.py", "*.sh", "*.md",
    )
    hits = [
        line for line in result.stdout.strip().splitlines()
        if line and not re.search(r"example|template|dummy|placeholder|spec/|pipeline", line)
    ]
    if hits:
        print("WARNING: Found possible secrets in tracked files")
        for h in hits:
            print(f"  {h}")
        return 1
    print("OK: No secrets patterns found")
    return 0


def _check_gitignore() -> int:
    issues = 0
    for path in GITIGNORE_REQUIRED:
        result = _git("check-ignore", path)
        if result.returncode != 0:
            print(f"CRITICAL: {path} is NOT gitignored!")
            issues += 1
        else:
            print(f"OK: {path} is gitignored")
    return issues


def _run_openclaw_audit() -> int:
    openclaw_bin = shutil.which("openclaw") or "openclaw"
    if not shutil.which(openclaw_bin):
        print("SKIP: openclaw CLI not found")
        return 0
    result = subprocess.run(
        [openclaw_bin, "security", "audit", "--deep"],
        capture_output=False, text=True,
    )
    return 0 if result.returncode == 0 else 1


def main() -> None:
    """Run the full security audit."""
    from datetime import datetime

    print("=== OpenClaw Security Audit ===")
    print(f"Date: {datetime.now():%c}")
    print()

    print("--- Checking for sensitive data in git-tracked files ---")
    issues = 0
    issues += _check_hardcoded_paths()
    issues += _check_phone_numbers()
    issues += _check_secrets_patterns()
    issues += _check_gitignore()
    print()

    print("--- OpenClaw Security Audit ---")
    issues += _run_openclaw_audit()
    print()

    print(f"=== Audit complete: {issues} issue(s) found ===")
    sys.exit(issues)


if __name__ == "__main__":
    main()
