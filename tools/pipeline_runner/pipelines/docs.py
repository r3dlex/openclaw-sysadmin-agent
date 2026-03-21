"""Docs pipeline — verifies internal markdown links and checks for stale TODOs."""

from __future__ import annotations

import re
from pathlib import Path

from tools.pipeline_runner.runner import PipelineResult

REPO_ROOT = Path(__file__).resolve().parents[3]

# Link pattern: [text](relative-path) — excludes http(s) and anchor-only links
LINK_RE = re.compile(r"\]\(([^)]+)\)")


def _check_internal_links() -> tuple[list[str], list[str]]:
    """Verify all relative markdown links resolve to real files."""
    errors, warnings = [], []
    for md_file in REPO_ROOT.rglob("*.md"):
        if ".git" in md_file.parts:
            continue
        content = md_file.read_text(errors="replace")
        for match in LINK_RE.finditer(content):
            target = match.group(1)
            # Skip external URLs, anchors, and mailto links
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            # Strip anchor from path
            path_part = target.split("#")[0]
            if not path_part:
                continue
            # Must look like a file reference (contains / or has extension)
            if "/" not in path_part and "." not in path_part:
                continue
            resolved = (md_file.parent / path_part).resolve()
            if not resolved.exists():
                rel = md_file.relative_to(REPO_ROOT)
                warnings.append(f"{rel}: broken link → {target}")
    return errors, warnings


def _check_todo_markers() -> tuple[list[str], list[str]]:
    """Warn on stale TODO/FIXME/HACK markers in docs."""
    warnings = []
    marker_re = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
    # Skip docs that legitimately reference these markers
    skip_files = {"PIPELINES.md", "TESTING.md", "ARCHITECTURE.md"}

    for md_file in REPO_ROOT.rglob("*.md"):
        if ".git" in md_file.parts:
            continue
        if md_file.name in skip_files:
            continue
        content = md_file.read_text(errors="replace")
        in_code_block = False
        for i, line in enumerate(content.splitlines(), 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if marker_re.search(line):
                rel = md_file.relative_to(REPO_ROOT)
                warnings.append(f"{rel}:{i}: {line.strip()}")
    return [], warnings


def run() -> PipelineResult:
    """Run all doc checks."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    checks = [
        ("Internal links", _check_internal_links),
        ("TODO markers", _check_todo_markers),
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
        name="Docs",
        passed=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings,
    )
