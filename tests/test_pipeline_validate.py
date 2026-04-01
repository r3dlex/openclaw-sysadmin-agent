"""Unit tests for tools.pipeline_runner.pipelines.validate."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.pipeline_runner.pipelines import validate
from tools.pipeline_runner.runner import PipelineResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _proc(stdout: str = "", returncode: int = 0, stderr: str = "") -> MagicMock:
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


# ---------------------------------------------------------------------------
# _lint_shell()
# ---------------------------------------------------------------------------


class TestLintShell:
    def test_no_warnings_when_shellcheck_passes(self) -> None:
        with patch("subprocess.run", return_value=_proc(returncode=0)):
            errors, warnings = validate._lint_shell()
        assert errors == []
        # warnings may or may not be empty depending on SHELL_SCRIPTS count

    def test_warning_when_shellcheck_fails(self) -> None:
        # Patch SHELL_SCRIPTS to have one item so shellcheck runs
        fake_script = MagicMock(spec=Path)
        fake_script.name = "test.sh"
        with (
            patch.object(validate, "SHELL_SCRIPTS", [fake_script]),
            patch("subprocess.run", return_value=_proc(returncode=1)),
        ):
            errors, warnings = validate._lint_shell()
        assert errors == []
        assert any("test.sh" in w for w in warnings)

    def test_no_scripts_means_no_warnings(self) -> None:
        with patch.object(validate, "SHELL_SCRIPTS", []):
            errors, warnings = validate._lint_shell()
        assert errors == []
        assert warnings == []


# ---------------------------------------------------------------------------
# _lint_python()
# ---------------------------------------------------------------------------


class TestLintPython:
    def test_no_errors_when_syntax_ok_and_ruff_clean(self) -> None:
        fake_script = MagicMock(spec=Path)
        fake_script.relative_to.return_value = Path("tools/test.py")
        with (
            patch.object(validate, "PYTHON_SCRIPTS", [fake_script]),
            patch("subprocess.run", return_value=_proc(returncode=0)),
        ):
            errors, warnings = validate._lint_python()
        assert errors == []

    def test_syntax_error_adds_to_errors(self) -> None:
        fake_script = MagicMock(spec=Path)
        fake_script.relative_to.return_value = Path("tools/bad.py")
        # First call = py_compile (fails), second call = ruff (passes)
        side_effects = [
            _proc(returncode=1, stderr="SyntaxError: invalid syntax"),
            _proc(returncode=0),
        ]
        with (
            patch.object(validate, "PYTHON_SCRIPTS", [fake_script]),
            patch("subprocess.run", side_effect=side_effects),
        ):
            errors, warnings = validate._lint_python()
        assert errors != []

    def test_ruff_failure_adds_warning(self) -> None:
        with (
            patch.object(validate, "PYTHON_SCRIPTS", []),
            patch("subprocess.run", return_value=_proc(returncode=1, stdout="E501 line too long")),
        ):
            errors, warnings = validate._lint_python()
        assert errors == []
        assert warnings != []


# ---------------------------------------------------------------------------
# _check_agent_files()
# ---------------------------------------------------------------------------


class TestCheckAgentFiles:
    def test_no_errors_when_all_files_exist(self, tmp_path: Path) -> None:
        for name in validate.REQUIRED_AGENT_FILES:
            f = tmp_path / name
            f.write_text("# content")
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, _ = validate._check_agent_files()
        assert errors == []

    def test_error_when_file_missing(self, tmp_path: Path) -> None:
        # Create all but one
        for name in validate.REQUIRED_AGENT_FILES[1:]:
            f = tmp_path / name
            f.write_text("# content")
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, _ = validate._check_agent_files()
        assert len(errors) >= 1

    def test_error_when_file_empty(self, tmp_path: Path) -> None:
        for name in validate.REQUIRED_AGENT_FILES:
            f = tmp_path / name
            f.write_text("")
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, _ = validate._check_agent_files()
        assert len(errors) == len(validate.REQUIRED_AGENT_FILES)

    @pytest.mark.parametrize("filename", validate.REQUIRED_AGENT_FILES)
    def test_each_required_file_is_checked(self, tmp_path: Path, filename: str) -> None:
        # All present and non-empty
        for name in validate.REQUIRED_AGENT_FILES:
            (tmp_path / name).write_text("# content")
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, _ = validate._check_agent_files()
        assert errors == []


# ---------------------------------------------------------------------------
# _check_spec_files()
# ---------------------------------------------------------------------------


class TestCheckSpecFiles:
    def test_no_errors_when_all_present(self, tmp_path: Path) -> None:
        for name in validate.REQUIRED_SPEC_FILES:
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# content")
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, _ = validate._check_spec_files()
        assert errors == []

    def test_error_when_spec_file_missing(self, tmp_path: Path) -> None:
        # Create all but the first
        for name in validate.REQUIRED_SPEC_FILES[1:]:
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# content")
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, _ = validate._check_spec_files()
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# _check_docker_build()
# ---------------------------------------------------------------------------


class TestCheckDockerBuild:
    def test_error_when_dockerfile_missing(self, tmp_path: Path) -> None:
        with patch.object(validate, "REPO_ROOT", tmp_path):
            errors, warnings = validate._check_docker_build()
        assert any("Dockerfile" in e for e in errors)

    def test_warning_when_docker_build_fails(self, tmp_path: Path) -> None:
        watchdog_dir = tmp_path / "watchdog"
        watchdog_dir.mkdir()
        (watchdog_dir / "Dockerfile").write_text("FROM ubuntu\n")
        with (
            patch.object(validate, "REPO_ROOT", tmp_path),
            patch("subprocess.run", return_value=_proc(returncode=1, stderr="no daemon")),
        ):
            errors, warnings = validate._check_docker_build()
        assert errors == []
        assert warnings != []

    def test_no_error_when_docker_succeeds(self, tmp_path: Path) -> None:
        watchdog_dir = tmp_path / "watchdog"
        watchdog_dir.mkdir()
        (watchdog_dir / "Dockerfile").write_text("FROM ubuntu\n")
        with (
            patch.object(validate, "REPO_ROOT", tmp_path),
            patch("subprocess.run", return_value=_proc(returncode=0)),
        ):
            errors, warnings = validate._check_docker_build()
        assert errors == []


# ---------------------------------------------------------------------------
# run() — full validate pipeline
# ---------------------------------------------------------------------------


class TestValidatePipelineRun:
    def test_passes_when_all_checks_clean(self, tmp_path: Path) -> None:
        clean = ([], [])
        with (
            patch.object(validate, "_lint_shell", return_value=clean),
            patch.object(validate, "_lint_python", return_value=clean),
            patch.object(validate, "_check_agent_files", return_value=clean),
            patch.object(validate, "_check_spec_files", return_value=clean),
            patch.object(validate, "_check_docker_build", return_value=clean),
        ):
            result = validate.run()
        assert result.passed is True

    def test_fails_when_any_check_has_error(self) -> None:
        clean = ([], [])
        error = (["critical error"], [])
        with (
            patch.object(validate, "_lint_shell", return_value=clean),
            patch.object(validate, "_lint_python", return_value=error),
            patch.object(validate, "_check_agent_files", return_value=clean),
            patch.object(validate, "_check_spec_files", return_value=clean),
            patch.object(validate, "_check_docker_build", return_value=clean),
        ):
            result = validate.run()
        assert result.passed is False

    def test_handles_file_not_found_gracefully(self) -> None:
        clean = ([], [])
        fnfe = FileNotFoundError("shellcheck")
        fnfe.filename = "shellcheck"
        with (
            patch.object(validate, "_lint_shell", side_effect=fnfe),
            patch.object(validate, "_lint_python", return_value=clean),
            patch.object(validate, "_check_agent_files", return_value=clean),
            patch.object(validate, "_check_spec_files", return_value=clean),
            patch.object(validate, "_check_docker_build", return_value=clean),
        ):
            result = validate.run()
        # FileNotFoundError → warning, not error
        assert result.passed is True
        assert len(result.warnings) >= 1

    def test_result_name_is_validate(self) -> None:
        clean = ([], [])
        with (
            patch.object(validate, "_lint_shell", return_value=clean),
            patch.object(validate, "_lint_python", return_value=clean),
            patch.object(validate, "_check_agent_files", return_value=clean),
            patch.object(validate, "_check_spec_files", return_value=clean),
            patch.object(validate, "_check_docker_build", return_value=clean),
        ):
            result = validate.run()
        assert result.name == "Validate"
