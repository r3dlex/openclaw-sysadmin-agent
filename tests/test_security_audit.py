"""Unit tests for tools.security_audit — sensitive-data scanning logic."""

from __future__ import annotations

import subprocess
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from tools import security_audit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_completed(stdout: str = "", returncode: int = 0) -> MagicMock:
    m = MagicMock(spec=subprocess.CompletedProcess)
    m.stdout = stdout
    m.returncode = returncode
    return m


# ---------------------------------------------------------------------------
# _git() helper
# ---------------------------------------------------------------------------


class TestGitHelper:
    def test_calls_subprocess_with_git(self) -> None:
        with patch("subprocess.run", return_value=_make_completed()) as mock_run:
            security_audit._git("grep", "-n", "foo")
        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert "grep" in args

    def test_passes_C_flag_with_repo_root(self) -> None:
        with patch("subprocess.run", return_value=_make_completed()) as mock_run:
            security_audit._git("status")
        args = mock_run.call_args[0][0]
        assert "-C" in args


# ---------------------------------------------------------------------------
# _check_hardcoded_paths()
# ---------------------------------------------------------------------------


class TestCheckHardcodedPaths:
    def test_returns_0_when_no_hits(self) -> None:
        with patch.object(security_audit, "_git", return_value=_make_completed("")):
            assert security_audit._check_hardcoded_paths() == 0

    def test_returns_1_when_real_path_found(self) -> None:
        output = "some_file.py:3:/Users/alice/secret"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_hardcoded_paths() == 1

    def test_ignores_template_lines(self) -> None:
        output = "template.md:1:/Users/example/template"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_hardcoded_paths() == 0

    def test_ignores_example_lines(self) -> None:
        output = "example.md:1:/Users/example/home"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_hardcoded_paths() == 0

    def test_ignores__home__placeholder(self) -> None:
        output = "BOOT.md:1:/Users/__HOME__/openclaw"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_hardcoded_paths() == 0

    @pytest.mark.parametrize("line,expected", [
        ("file.py:1:/Users/alice/code", 1),
        ("# grep /Users/ for paths", 0),   # grep pattern — filtered out
        ("TEMPLATE.md:1:/Users/TEMPLATE/x", 0),
    ])
    def test_parametrized_path_hits(self, line: str, expected: int) -> None:
        with patch.object(security_audit, "_git", return_value=_make_completed(line)):
            assert security_audit._check_hardcoded_paths() == expected


# ---------------------------------------------------------------------------
# _check_phone_numbers()
# ---------------------------------------------------------------------------


class TestCheckPhoneNumbers:
    def test_returns_0_when_no_phone(self) -> None:
        with patch.object(security_audit, "_git", return_value=_make_completed("")):
            assert security_audit._check_phone_numbers() == 0

    def test_returns_1_when_phone_found(self) -> None:
        output = "contact.md:5:+49123456789012"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_phone_numbers() == 1


# ---------------------------------------------------------------------------
# _check_secrets_patterns()
# ---------------------------------------------------------------------------


class TestCheckSecretsPatterns:
    def test_returns_0_when_no_secrets(self) -> None:
        with patch.object(security_audit, "_git", return_value=_make_completed("")):
            assert security_audit._check_secrets_patterns() == 0

    def test_returns_1_on_api_key_assignment(self) -> None:
        output = "config.py:10:api_key = 'abc123'"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_secrets_patterns() == 1

    def test_ignores_example_lines(self) -> None:
        output = "example.py:5:api_key = 'dummy'"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_secrets_patterns() == 0

    def test_ignores_template_lines(self) -> None:
        output = "template.md:2:password = 'placeholder'"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_secrets_patterns() == 0

    def test_ignores_spec_lines(self) -> None:
        output = "spec/PIPELINES.md:3:token = 'secret'"
        with patch.object(security_audit, "_git", return_value=_make_completed(output)):
            assert security_audit._check_secrets_patterns() == 0

    @pytest.mark.parametrize("line,expected", [
        ("real.py:1:api_key = 'real'", 1),
        ("spec/TESTING.md:1:token = 'x'", 0),
        ("pipeline.py:1:password = 'y'", 0),  # 'pipeline' in line → filtered
    ])
    def test_parametrized_secrets(self, line: str, expected: int) -> None:
        with patch.object(security_audit, "_git", return_value=_make_completed(line)):
            assert security_audit._check_secrets_patterns() == expected


# ---------------------------------------------------------------------------
# _check_gitignore()
# ---------------------------------------------------------------------------


class TestCheckGitignore:
    def test_returns_0_when_all_gitignored(self) -> None:
        ok = _make_completed(returncode=0)
        with patch.object(security_audit, "_git", return_value=ok):
            assert security_audit._check_gitignore() == 0

    def test_returns_issues_count_when_not_gitignored(self) -> None:
        fail = _make_completed(returncode=1)
        with patch.object(security_audit, "_git", return_value=fail):
            # GITIGNORE_REQUIRED has 4 entries
            result = security_audit._check_gitignore()
        assert result == len(security_audit.GITIGNORE_REQUIRED)

    def test_partial_failure_counts_correctly(self) -> None:
        ok = _make_completed(returncode=0)
        fail = _make_completed(returncode=1)
        side_effects = [ok, fail, ok, ok]
        with patch.object(security_audit, "_git", side_effect=side_effects):
            result = security_audit._check_gitignore()
        assert result == 1


# ---------------------------------------------------------------------------
# _run_openclaw_audit()
# ---------------------------------------------------------------------------


class TestRunOpenclawAudit:
    def test_skips_when_openclaw_not_found(self) -> None:
        with patch("shutil.which", return_value=None):
            result = security_audit._run_openclaw_audit()
        assert result == 0

    def test_returns_0_on_success(self) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/openclaw"),
            patch("subprocess.run", return_value=_make_completed(returncode=0)),
        ):
            result = security_audit._run_openclaw_audit()
        assert result == 0

    def test_returns_1_on_failure(self) -> None:
        with (
            patch("shutil.which", return_value="/usr/local/bin/openclaw"),
            patch("subprocess.run", return_value=_make_completed(returncode=1)),
        ):
            result = security_audit._run_openclaw_audit()
        assert result == 1


# ---------------------------------------------------------------------------
# main() — orchestration
# ---------------------------------------------------------------------------


class TestSecurityAuditMain:
    def test_exits_0_when_clean(self) -> None:
        with (
            patch.object(security_audit, "_check_hardcoded_paths", return_value=0),
            patch.object(security_audit, "_check_phone_numbers", return_value=0),
            patch.object(security_audit, "_check_secrets_patterns", return_value=0),
            patch.object(security_audit, "_check_gitignore", return_value=0),
            patch.object(security_audit, "_run_openclaw_audit", return_value=0),
            pytest.raises(SystemExit) as exc_info,
        ):
            security_audit.main()
        assert exc_info.value.code == 0

    def test_exits_nonzero_on_issues(self) -> None:
        with (
            patch.object(security_audit, "_check_hardcoded_paths", return_value=1),
            patch.object(security_audit, "_check_phone_numbers", return_value=0),
            patch.object(security_audit, "_check_secrets_patterns", return_value=1),
            patch.object(security_audit, "_check_gitignore", return_value=0),
            patch.object(security_audit, "_run_openclaw_audit", return_value=0),
            pytest.raises(SystemExit) as exc_info,
        ):
            security_audit.main()
        assert exc_info.value.code == 2

    def test_aggregates_all_issues(self) -> None:
        with (
            patch.object(security_audit, "_check_hardcoded_paths", return_value=2),
            patch.object(security_audit, "_check_phone_numbers", return_value=1),
            patch.object(security_audit, "_check_secrets_patterns", return_value=0),
            patch.object(security_audit, "_check_gitignore", return_value=3),
            patch.object(security_audit, "_run_openclaw_audit", return_value=0),
            pytest.raises(SystemExit) as exc_info,
        ):
            security_audit.main()
        assert exc_info.value.code == 6
