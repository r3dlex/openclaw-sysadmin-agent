"""Pipeline orchestration — discovers and runs pipeline modules."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class PipelineResult:
    """Result of a single pipeline run."""

    name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_s: float = 0.0

    @property
    def status_icon(self) -> str:
        if not self.passed:
            return "FAIL"
        if self.warnings:
            return "WARN"
        return "OK"


def run_pipeline(name: str, func: object) -> PipelineResult:
    """Run a single pipeline function and capture its result."""
    start = time.monotonic()
    try:
        result = func()  # type: ignore[operator]
        if not isinstance(result, PipelineResult):
            result = PipelineResult(name=name, passed=True)
    except Exception as exc:
        result = PipelineResult(name=name, passed=False, errors=[str(exc)])
    result.duration_s = time.monotonic() - start
    return result


def print_summary(results: Sequence[PipelineResult]) -> None:
    """Print a summary table of all pipeline results."""
    print("\n" + "=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    for r in results:
        icon = r.status_icon
        print(f"  [{icon:>4}] {r.name} ({r.duration_s:.1f}s)")
        for err in r.errors:
            print(f"         ERROR: {err}")
        for warn in r.warnings:
            print(f"         WARN:  {warn}")
    print("=" * 60)

    failed = sum(1 for r in results if not r.passed)
    warned = sum(1 for r in results if r.passed and r.warnings)
    total = len(results)
    print(f"  {total} pipelines: {total - failed - warned} passed, {warned} warned, {failed} failed")

    if failed:
        sys.exit(1)
