"""CLI entry point for the pipeline runner.

Usage:
    oc-pipeline                     # Run all pipelines
    oc-pipeline security            # Run only security pipeline
    oc-pipeline validate docs       # Run specific pipelines
    oc-pipeline --list              # List available pipelines
    python -m tools.pipeline_runner # Same as oc-pipeline
"""

from __future__ import annotations

import argparse
import sys

from tools.pipeline_runner.pipelines import security, validate, docs, iamq
from tools.pipeline_runner.runner import run_pipeline, print_summary

PIPELINES: dict[str, object] = {
    "security": security.run,
    "validate": validate.run,
    "docs": docs.run,
    "iamq": iamq.run,
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="oc-pipeline",
        description="Run CI/CD pipelines for the OpenClaw sysadmin agent.",
    )
    parser.add_argument(
        "pipelines",
        nargs="*",
        choices=[*PIPELINES.keys(), []],
        default=[],
        help="Pipelines to run (default: all)",
    )
    parser.add_argument("--list", action="store_true", help="List available pipelines")
    args = parser.parse_args(argv)

    if args.list:
        print("Available pipelines:")
        for name in PIPELINES:
            print(f"  - {name}")
        return

    selected = args.pipelines or list(PIPELINES.keys())
    results = []
    for name in selected:
        func = PIPELINES[name]
        print(f"\n--- Running: {name} ---")
        result = run_pipeline(name, func)
        results.append(result)

    print_summary(results)


if __name__ == "__main__":
    main()
