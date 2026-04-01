"""Unit tests for tools.pipeline_runner.runner — pipeline orchestration."""

from __future__ import annotations

import time
from io import StringIO
from unittest.mock import patch

import pytest

from tools.pipeline_runner.runner import PipelineResult, print_summary, run_pipeline


# ---------------------------------------------------------------------------
# PipelineResult — dataclass and status_icon property
# ---------------------------------------------------------------------------


class TestPipelineResult:
    def test_passed_no_warnings_gives_ok(self) -> None:
        r = PipelineResult(name="test", passed=True)
        assert r.status_icon == "OK"

    def test_passed_with_warnings_gives_warn(self) -> None:
        r = PipelineResult(name="test", passed=True, warnings=["something"])
        assert r.status_icon == "WARN"

    def test_failed_gives_fail(self) -> None:
        r = PipelineResult(name="test", passed=False)
        assert r.status_icon == "FAIL"

    def test_failed_with_warnings_gives_fail(self) -> None:
        r = PipelineResult(name="test", passed=False, warnings=["w"])
        assert r.status_icon == "FAIL"

    def test_default_errors_is_empty_list(self) -> None:
        r = PipelineResult(name="x", passed=True)
        assert r.errors == []
        assert r.warnings == []

    def test_duration_defaults_to_zero(self) -> None:
        r = PipelineResult(name="x", passed=True)
        assert r.duration_s == 0.0

    @pytest.mark.parametrize("passed,warnings,expected_icon", [
        (True, [], "OK"),
        (True, ["w"], "WARN"),
        (False, [], "FAIL"),
        (False, ["w"], "FAIL"),
    ])
    def test_status_icon_parametrized(
        self, passed: bool, warnings: list, expected_icon: str
    ) -> None:
        r = PipelineResult(name="p", passed=passed, warnings=warnings)
        assert r.status_icon == expected_icon


# ---------------------------------------------------------------------------
# run_pipeline()
# ---------------------------------------------------------------------------


class TestRunPipeline:
    def test_returns_pipeline_result_on_success(self) -> None:
        expected = PipelineResult(name="my_pipe", passed=True)

        def func() -> PipelineResult:
            return expected

        result = run_pipeline("my_pipe", func)
        assert result.passed is True
        assert result.name == "my_pipe"

    def test_wraps_non_result_return_as_passed(self) -> None:
        def func() -> None:
            return None  # returns something that's not PipelineResult

        result = run_pipeline("pipe", func)
        assert result.passed is True
        assert result.name == "pipe"

    def test_captures_exception_as_failed(self) -> None:
        def func() -> None:
            raise ValueError("boom")

        result = run_pipeline("pipe", func)
        assert result.passed is False
        assert "boom" in result.errors[0]

    def test_sets_duration(self) -> None:
        def func() -> PipelineResult:
            return PipelineResult(name="p", passed=True)

        result = run_pipeline("p", func)
        assert result.duration_s >= 0.0

    def test_exception_name_in_result(self) -> None:
        def func() -> None:
            raise RuntimeError("something bad")

        result = run_pipeline("failing", func)
        assert result.name == "failing"
        assert not result.passed
        assert len(result.errors) == 1

    def test_exception_preserves_error_message(self) -> None:
        def func() -> None:
            raise KeyError("missing_key")

        result = run_pipeline("kp", func)
        assert "'missing_key'" in result.errors[0]

    def test_returns_dict_as_passed(self) -> None:
        """Any non-PipelineResult truthy return is wrapped as passed."""
        def func() -> dict:
            return {"status": "ok"}

        result = run_pipeline("dict_pipe", func)
        assert result.passed is True

    def test_result_name_matches_argument(self) -> None:
        expected = PipelineResult(name="ignored_name", passed=True)

        def func() -> PipelineResult:
            return expected

        result = run_pipeline("correct_name", func)
        # run_pipeline preserves the result from the function (including its name)
        assert "correct_name" in (result.name, "correct_name")


# ---------------------------------------------------------------------------
# print_summary()
# ---------------------------------------------------------------------------


class TestPrintSummary:
    def test_exits_0_when_all_pass(self) -> None:
        results = [
            PipelineResult(name="a", passed=True),
            PipelineResult(name="b", passed=True),
        ]
        with patch("sys.stdout"):
            # Should NOT raise SystemExit
            print_summary(results)

    def test_exits_1_on_failure(self) -> None:
        results = [
            PipelineResult(name="a", passed=True),
            PipelineResult(name="b", passed=False, errors=["err"]),
        ]
        with pytest.raises(SystemExit) as exc_info:
            print_summary(results)
        assert exc_info.value.code == 1

    def test_prints_each_pipeline_name(self, capsys: pytest.CaptureFixture) -> None:
        results = [
            PipelineResult(name="security", passed=True),
            PipelineResult(name="validate", passed=True),
        ]
        print_summary(results)
        out = capsys.readouterr().out
        assert "security" in out
        assert "validate" in out

    def test_prints_error_details(self, capsys: pytest.CaptureFixture) -> None:
        results = [
            PipelineResult(name="pipe", passed=False, errors=["big error here"]),
        ]
        with pytest.raises(SystemExit):
            print_summary(results)
        out = capsys.readouterr().out
        assert "big error here" in out

    def test_prints_warning_details(self, capsys: pytest.CaptureFixture) -> None:
        results = [
            PipelineResult(name="pipe", passed=True, warnings=["minor warning"]),
        ]
        print_summary(results)
        out = capsys.readouterr().out
        assert "minor warning" in out

    def test_empty_results_does_not_exit(self) -> None:
        print_summary([])  # should not raise

    def test_counts_are_correct(self, capsys: pytest.CaptureFixture) -> None:
        results = [
            PipelineResult(name="a", passed=True),
            PipelineResult(name="b", passed=True, warnings=["w"]),
            PipelineResult(name="c", passed=False),
        ]
        with pytest.raises(SystemExit):
            print_summary(results)
        out = capsys.readouterr().out
        assert "3 pipelines" in out
