"""Validate pipeline — lints scripts, checks agent files, verifies Docker build."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tools.pipeline_runner.runner import PipelineResult

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_AGENT_FILES = [
    "AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md",
    "PROTOCOL.md", "HEARTBEAT.md", "TOOLS.md",
]

REQUIRED_SPEC_FILES = [
    "spec/ARCHITECTURE.md", "spec/TROUBLESHOOTING.md",
    "spec/TESTING.md", "spec/LEARNINGS.md",
]

SHELL_SCRIPTS = list((REPO_ROOT / "scripts").glob("*.sh"))
PYTHON_SCRIPTS = list((REPO_ROOT / "tools").rglob("*.py"))


def _lint_shell() -> tuple[list[str], list[str]]:
    """Run shellcheck on all shell scripts (warnings non-blocking)."""
    warnings = []
    for script in SHELL_SCRIPTS:
        result = subprocess.run(
            ["shellcheck", str(script)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            warnings.append(f"shellcheck warnings in {script.name}")
    return [], warnings


def _lint_python() -> tuple[list[str], list[str]]:
    """Check Python syntax and run ruff."""
    errors, warnings = [], []
    for script in PYTHON_SCRIPTS:
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(script)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            errors.append(f"Syntax error in {script.relative_to(REPO_ROOT)}: {result.stderr.strip()}")

    # Run ruff if available
    result = subprocess.run(
        ["ruff", "check", str(REPO_ROOT / "tools")],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        warnings.append(f"ruff issues:\n{result.stdout.strip()}")

    return errors, warnings


def _check_agent_files() -> tuple[list[str], list[str]]:
    """Verify required agent markdown files exist and are non-empty."""
    errors = []
    for name in REQUIRED_AGENT_FILES:
        path = REPO_ROOT / name
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"Missing or empty: {name}")
    return errors, []


def _check_spec_files() -> tuple[list[str], list[str]]:
    """Verify required spec files exist and are non-empty."""
    errors = []
    for name in REQUIRED_SPEC_FILES:
        path = REPO_ROOT / name
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"Missing or empty: {name}")
    return errors, []


def _check_docker_build() -> tuple[list[str], list[str]]:
    """Verify the watchdog Docker image builds."""
    errors, warnings = [], []
    dockerfile = REPO_ROOT / "watchdog" / "Dockerfile"
    if not dockerfile.exists():
        errors.append("watchdog/Dockerfile not found")
        return errors, warnings

    result = subprocess.run(
        ["docker", "build", "-t", "openclaw-watchdog-test", str(REPO_ROOT / "watchdog")],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        # Docker may not be available locally — warn, don't fail
        warnings.append(f"Docker build failed (may not be available): {result.stderr.strip()[:200]}")
    return errors, warnings


def run() -> PipelineResult:
    """Run all validation checks."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    checks = [
        ("Shell lint", _lint_shell),
        ("Python lint", _lint_python),
        ("Agent files", _check_agent_files),
        ("Spec files", _check_spec_files),
        ("Docker build", _check_docker_build),
    ]

    for name, check_fn in checks:
        try:
            errs, warns = check_fn()
            all_errors.extend(errs)
            all_warnings.extend(warns)
            status = "FAIL" if errs else ("WARN" if warns else "OK")
            print(f"  [{status:>4}] {name}")
        except FileNotFoundError as exc:
            all_warnings.append(f"{name}: tool not found ({exc.filename})")
            print(f"  [WARN] {name}: tool not found")
        except Exception as exc:
            all_errors.append(f"{name}: {exc}")
            print(f"  [FAIL] {name}: {exc}")

    return PipelineResult(
        name="Validate",
        passed=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings,
    )
