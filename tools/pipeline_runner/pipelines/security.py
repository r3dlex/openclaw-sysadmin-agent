"""Security audit pipeline — scans for sensitive data in code and git history."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tools.pipeline_runner.runner import PipelineResult

REPO_ROOT = Path(__file__).resolve().parents[3]

# Paths to exclude from scans (relative to repo root)
EXCLUDE_PATHS = {
    ".gitignore",
    "scripts/security-audit.sh",
    "spec/TESTING.md",
    "spec/PIPELINES.md",
    "tools/pipeline_runner/pipelines/security.py",
    "tools/security_audit.py",
}

EXCLUDE_GLOBS_GIT = [
    ":(exclude).gitignore",
    ":(exclude)scripts/security-audit.sh",
    ":(exclude)spec/TESTING.md",
    ":(exclude)spec/PIPELINES.md",
    ":(exclude).github/",
    ":(exclude)tools/pipeline_runner/",
    ":(exclude)tools/security_audit.py",
    ":(exclude)tests/",
]

GITIGNORE_REQUIRED = [".env", "logs/", "archive/", ".openclaw/"]


def _git_grep(pattern: str, extra_args: list[str] | None = None) -> list[str]:
    """Run git grep and return matching lines."""
    cmd = ["git", "-C", str(REPO_ROOT), "grep", "-n", *pattern.split()]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return [line for line in result.stdout.strip().splitlines() if line]


def _check_hardcoded_paths() -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    cmd = [
        "git", "-C", str(REPO_ROOT), "grep", "-n", "/Users/",
        "--", *EXCLUDE_GLOBS_GIT,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    hits = [
        line for line in result.stdout.strip().splitlines()
        if line and not re.search(r"template|example|TEMPLATE|__HOME__|grep.*Users", line)
    ]
    if hits:
        errors.append(f"Hardcoded /Users/ paths found:\n" + "\n".join(f"  {h}" for h in hits))
    return errors, warnings


def _check_phone_numbers() -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    cmd = [
        "git", "-C", str(REPO_ROOT), "grep", "-nE", r"\+[0-9]{10,}",
        "--", ":(exclude).env.example", ":(exclude).github/",
        ":(exclude)tools/pipeline_runner/",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout.strip():
        errors.append("Phone numbers found in tracked files")
    return errors, warnings


def _check_secrets_patterns() -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    cmd = [
        "git", "-C", str(REPO_ROOT), "grep", "-nEi",
        r"(api_key|secret_key|password|token)\s*=",
        "--", "*.py", "*.sh", "*.md", ":(exclude)tests/",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    hits = [
        line for line in result.stdout.strip().splitlines()
        if line and not re.search(r"example|template|dummy|placeholder|spec/|pipeline", line)
    ]
    if hits:
        errors.append(f"Secret patterns found:\n" + "\n".join(f"  {h}" for h in hits))
    return errors, warnings


def _check_gitignore() -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for path in GITIGNORE_REQUIRED:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "check-ignore", path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            errors.append(f"{path} is NOT gitignored")
    return errors, warnings


def _check_git_history() -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    # Scan recent history for real phone numbers (not dummy +1234567890)
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "--all", "-p", "--diff-filter=A"],
        capture_output=True, text=True, timeout=30,
    )
    for line in result.stdout.splitlines():
        if line.startswith("+") and re.search(r"\+49[0-9]{8,}", line):
            if not re.search(r"grep|example|dummy", line):
                warnings.append("Possible phone number in git history")
                break
    return errors, warnings


def run() -> PipelineResult:
    """Run all security checks."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    checks = [
        ("Hardcoded paths", _check_hardcoded_paths),
        ("Phone numbers", _check_phone_numbers),
        ("Secret patterns", _check_secrets_patterns),
        ("Gitignore rules", _check_gitignore),
        ("Git history", _check_git_history),
    ]

    for name, check_fn in checks:
        try:
            errs, warns = check_fn()
            all_errors.extend(errs)
            all_warnings.extend(warns)
            status = "FAIL" if errs else ("WARN" if warns else "OK")
            print(f"  [{status:>4}] {name}")
        except Exception as exc:
            all_errors.append(f"{name}: {exc}")
            print(f"  [FAIL] {name}: {exc}")

    return PipelineResult(
        name="Security Audit",
        passed=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings,
    )
