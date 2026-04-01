"""Unit tests for tools.pipeline_runner.pipelines.security."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from tools.pipeline_runner.pipelines import security
from tools.pipeline_runner.runner import PipelineResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _proc(stdout: str = "", returncode: int = 0) -> MagicMock:
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.stdout = stdout
    m.returncode = returncode
    return m


# ---------------------------------------------------------------------------
# _git_grep()
# ---------------------------------------------------------------------------


class TestGitGrep:
    def test_returns_matching_lines(self) -> None:
        with patch("subprocess.run", return_value=_proc("file.py:1:match\nfile.py:2:match2")):
            lines = security._git_grep("/Users/", extra_args=[])
        assert len(lines) == 2

    def test_filters_empty_lines(self) -> None:
        with patch("subprocess.run", return_value=_proc("\n\n\n")):
            lines = security._git_grep("/Users/")
        assert lines == []

    def test_no_extra_args(self) -> None:
        with patch("subprocess.run", return_value=_proc("")) as mock_run:
            security._git_grep("pattern")
        cmd = mock_run.call_args[0][0]
        assert "pattern" in cmd


# ---------------------------------------------------------------------------
# _check_hardcoded_paths()
# ---------------------------------------------------------------------------


class TestCheckHardcodedPaths:
    def test_returns_no_errors_when_clean(self) -> None:
        with patch("subprocess.run", return_value=_proc("")):
            errors, warnings = security._check_hardcoded_paths()
        assert errors == []
        assert warnings == []

    def test_returns_error_when_real_path_found(self) -> None:
        output = "tools/iamq.py:5:/Users/alice/secret"
        with patch("subprocess.run", return_value=_proc(output)):
            errors, warnings = security._check_hardcoded_paths()
        assert len(errors) == 1

    def test_ignores_template_path(self) -> None:
        output = "docs/BOOT.md:1:/Users/template/thing"
        with patch("subprocess.run", return_value=_proc(output)):
            errors, warnings = security._check_hardcoded_paths()
        assert errors == []

    def test_ignores_example_path(self) -> None:
        output = "example.md:1:/Users/example/path"
        with patch("subprocess.run", return_value=_proc(output)):
            errors, warnings = security._check_hardcoded_paths()
        assert errors == []


# ---------------------------------------------------------------------------
# _check_phone_numbers()
# ---------------------------------------------------------------------------


class TestCheckPhoneNumbers:
    def test_returns_error_when_phone_found(self) -> None:
        with patch("subprocess.run", return_value=_proc("+49123456789012")):
            errors, _ = security._check_phone_numbers()
        assert errors != []

    def test_returns_no_error_when_clean(self) -> None:
        with patch("subprocess.run", return_value=_proc("")):
            errors, _ = security._check_phone_numbers()
        assert errors == []


# ---------------------------------------------------------------------------
# _check_secrets_patterns()
# ---------------------------------------------------------------------------


class TestCheckSecretsPatterns:
    def test_no_errors_when_clean(self) -> None:
        with patch("subprocess.run", return_value=_proc("")):
            errors, _ = security._check_secrets_patterns()
        assert errors == []

    def test_error_on_real_secret(self) -> None:
        with patch("subprocess.run", return_value=_proc("config.py:1:api_key = 'secret'")):
            errors, _ = security._check_secrets_patterns()
        assert errors != []

    def test_ignores_spec_file(self) -> None:
        with patch("subprocess.run", return_value=_proc("spec/TESTING.md:1:token = 'x'")):
            errors, _ = security._check_secrets_patterns()
        assert errors == []

    def test_ignores_pipeline_reference(self) -> None:
        with patch("subprocess.run", return_value=_proc("pipeline.py:1:password = 'y'")):
            errors, _ = security._check_secrets_patterns()
        assert errors == []


# ---------------------------------------------------------------------------
# _check_gitignore()
# ---------------------------------------------------------------------------


class TestCheckGitignore:
    def test_no_errors_when_all_ignored(self) -> None:
        with patch("subprocess.run", return_value=_proc(returncode=0)):
            errors, _ = security._check_gitignore()
        assert errors == []

    def test_errors_when_not_ignored(self) -> None:
        with patch("subprocess.run", return_value=_proc(returncode=1)):
            errors, _ = security._check_gitignore()
        assert len(errors) == len(security.GITIGNORE_REQUIRED)

    @pytest.mark.parametrize("path", security.GITIGNORE_REQUIRED)
    def test_each_required_path_checked(self, path: str) -> None:
        calls = []

        def side_effect(cmd, **kwargs):
            calls.append(cmd)
            return _proc(returncode=0)

        with patch("subprocess.run", side_effect=side_effect):
            security._check_gitignore()

        checked = [" ".join(c) for c in calls]
        assert any(path in c for c in checked)


# ---------------------------------------------------------------------------
# _check_git_history()
# ---------------------------------------------------------------------------


class TestCheckGitHistory:
    def test_no_warnings_when_clean(self) -> None:
        with patch("subprocess.run", return_value=_proc("")):
            errors, warnings = security._check_git_history()
        assert errors == []
        assert warnings == []

    def test_warns_on_german_phone_in_history(self) -> None:
        output = "+49123456789\n"
        with patch("subprocess.run", return_value=_proc(output)):
            errors, warnings = security._check_git_history()
        assert warnings != []

    def test_ignores_dummy_number(self) -> None:
        output = "+49123456789 dummy example\n"
        with patch("subprocess.run", return_value=_proc(output)):
            errors, warnings = security._check_git_history()
        assert warnings == []


# ---------------------------------------------------------------------------
# run() — full security pipeline
# ---------------------------------------------------------------------------


class TestSecurityPipelineRun:
    def test_passes_when_all_checks_clean(self) -> None:
        clean = ([], [])
        with patch.object(security, "_check_hardcoded_paths", return_value=clean), \
             patch.object(security, "_check_phone_numbers", return_value=clean), \
             patch.object(security, "_check_secrets_patterns", return_value=clean), \
             patch.object(security, "_check_gitignore", return_value=clean), \
             patch.object(security, "_check_git_history", return_value=clean):
            result = security.run()
        assert result.passed is True
        assert result.errors == []

    def test_fails_when_error_raised(self) -> None:
        error = (["hardcoded path found"], [])
        clean = ([], [])
        with patch.object(security, "_check_hardcoded_paths", return_value=error), \
             patch.object(security, "_check_phone_numbers", return_value=clean), \
             patch.object(security, "_check_secrets_patterns", return_value=clean), \
             patch.object(security, "_check_gitignore", return_value=clean), \
             patch.object(security, "_check_git_history", return_value=clean):
            result = security.run()
        assert result.passed is False
        assert len(result.errors) == 1

    def test_collects_warnings(self) -> None:
        warn = ([], ["minor warning"])
        clean = ([], [])
        with patch.object(security, "_check_hardcoded_paths", return_value=clean), \
             patch.object(security, "_check_phone_numbers", return_value=clean), \
             patch.object(security, "_check_secrets_patterns", return_value=clean), \
             patch.object(security, "_check_gitignore", return_value=clean), \
             patch.object(security, "_check_git_history", return_value=warn):
            result = security.run()
        assert result.passed is True
        assert "minor warning" in result.warnings

    def test_exception_in_check_adds_error(self) -> None:
        with patch.object(security, "_check_hardcoded_paths", side_effect=RuntimeError("boom")), \
             patch.object(security, "_check_phone_numbers", return_value=([], [])), \
             patch.object(security, "_check_secrets_patterns", return_value=([], [])), \
             patch.object(security, "_check_gitignore", return_value=([], [])), \
             patch.object(security, "_check_git_history", return_value=([], [])):
            result = security.run()
        assert result.passed is False
        assert any("boom" in e for e in result.errors)

    def test_result_has_correct_name(self) -> None:
        clean = ([], [])
        with patch.object(security, "_check_hardcoded_paths", return_value=clean), \
             patch.object(security, "_check_phone_numbers", return_value=clean), \
             patch.object(security, "_check_secrets_patterns", return_value=clean), \
             patch.object(security, "_check_gitignore", return_value=clean), \
             patch.object(security, "_check_git_history", return_value=clean):
            result = security.run()
        assert result.name == "Security Audit"
