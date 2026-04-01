"""Unit tests for tools.pipeline_runner.cli — CLI argument parsing and dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.pipeline_runner import cli
from tools.pipeline_runner.runner import PipelineResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok_result(name: str) -> PipelineResult:
    return PipelineResult(name=name, passed=True)


def _fail_result(name: str) -> PipelineResult:
    return PipelineResult(name=name, passed=False, errors=["test error"])


# ---------------------------------------------------------------------------
# main() — --list flag
# ---------------------------------------------------------------------------


class TestListFlag:
    def test_list_prints_available_pipelines(self, capsys: pytest.CaptureFixture) -> None:
        cli.main(["--list"])
        out = capsys.readouterr().out
        for name in cli.PIPELINES:
            assert name in out

    def test_list_does_not_run_pipelines(self) -> None:
        with patch("tools.pipeline_runner.cli.run_pipeline") as mock_run:
            cli.main(["--list"])
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# main() — pipeline selection
# ---------------------------------------------------------------------------


class TestPipelineSelection:
    def test_runs_all_pipelines_by_default(self) -> None:
        mock_result = _ok_result("x")
        with (
            patch("tools.pipeline_runner.cli.run_pipeline", return_value=mock_result) as mock_run,
            patch("tools.pipeline_runner.cli.print_summary"),
        ):
            cli.main([])
        assert mock_run.call_count == len(cli.PIPELINES)

    def test_runs_single_named_pipeline(self) -> None:
        mock_result = _ok_result("security")
        with (
            patch("tools.pipeline_runner.cli.run_pipeline", return_value=mock_result) as mock_run,
            patch("tools.pipeline_runner.cli.print_summary"),
        ):
            cli.main(["security"])
        assert mock_run.call_count == 1
        assert mock_run.call_args[0][0] == "security"

    def test_runs_multiple_named_pipelines(self) -> None:
        mock_result = _ok_result("x")
        with (
            patch("tools.pipeline_runner.cli.run_pipeline", return_value=mock_result) as mock_run,
            patch("tools.pipeline_runner.cli.print_summary"),
        ):
            cli.main(["security", "validate"])
        assert mock_run.call_count == 2

    def test_invalid_pipeline_exits(self) -> None:
        with pytest.raises(SystemExit):
            cli.main(["nonexistent_pipeline"])

    def test_print_summary_called_with_results(self) -> None:
        mock_result = _ok_result("docs")
        with (
            patch("tools.pipeline_runner.cli.run_pipeline", return_value=mock_result),
            patch("tools.pipeline_runner.cli.print_summary") as mock_summary,
        ):
            cli.main(["docs"])
        mock_summary.assert_called_once()
        args = mock_summary.call_args[0][0]
        assert isinstance(args, list)
        assert len(args) == 1


# ---------------------------------------------------------------------------
# PIPELINES registry
# ---------------------------------------------------------------------------


class TestPipelinesRegistry:
    def test_all_expected_pipelines_registered(self) -> None:
        expected = {"security", "validate", "docs", "iamq"}
        assert expected.issubset(set(cli.PIPELINES.keys()))

    def test_all_pipeline_funcs_are_callable(self) -> None:
        for name, func in cli.PIPELINES.items():
            assert callable(func), f"Pipeline '{name}' is not callable"
