"""Unit tests for tools.pipeline_runner.pipelines.iamq — IAMQ health checks."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from tools.pipeline_runner.pipelines import iamq
from tools.pipeline_runner.runner import PipelineResult


# ---------------------------------------------------------------------------
# _get()
# ---------------------------------------------------------------------------


class TestGet:
    def test_returns_none_on_url_error(self) -> None:
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("unreachable")):
            result = iamq._get("/status")
        assert result is None

    def test_returns_none_on_timeout(self) -> None:
        with patch("urllib.request.urlopen", side_effect=TimeoutError()):
            result = iamq._get("/status")
        assert result is None

    def test_returns_parsed_json_on_success(self) -> None:
        import json
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"status": "ok"}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = iamq._get("/status")
        assert result == {"status": "ok"}


# ---------------------------------------------------------------------------
# _check_reachable()
# ---------------------------------------------------------------------------


class TestCheckReachable:
    def test_error_when_unreachable(self) -> None:
        with patch.object(iamq, "_get", return_value=None):
            errors, warnings = iamq._check_reachable()
        assert errors != []

    def test_no_error_when_reachable(self) -> None:
        with patch.object(iamq, "_get", return_value={"status": "ok"}):
            errors, warnings = iamq._check_reachable()
        assert errors == []
        assert warnings == []


# ---------------------------------------------------------------------------
# _check_agent_registered()
# ---------------------------------------------------------------------------


class TestCheckAgentRegistered:
    def test_warning_when_iamq_unreachable(self) -> None:
        with patch.object(iamq, "_get", return_value=None):
            errors, warnings = iamq._check_agent_registered()
        assert errors == []
        assert warnings != []

    def test_warning_when_agent_not_in_list(self) -> None:
        response = {"agents": [{"id": "other_agent"}]}
        with patch.object(iamq, "_get", return_value=response):
            errors, warnings = iamq._check_agent_registered()
        assert errors == []
        assert warnings != []

    def test_no_warning_when_agent_registered(self) -> None:
        response = {"agents": [{"id": iamq.AGENT_ID}]}
        with patch.object(iamq, "_get", return_value=response):
            errors, warnings = iamq._check_agent_registered()
        assert errors == []
        assert warnings == []

    def test_no_warning_when_multiple_agents_including_ours(self) -> None:
        response = {"agents": [{"id": "other"}, {"id": iamq.AGENT_ID}]}
        with patch.object(iamq, "_get", return_value=response):
            errors, warnings = iamq._check_agent_registered()
        assert warnings == []


# ---------------------------------------------------------------------------
# _check_unread_messages()
# ---------------------------------------------------------------------------


class TestCheckUnreadMessages:
    def test_warning_when_iamq_unreachable(self) -> None:
        with patch.object(iamq, "_get", return_value=None):
            errors, warnings = iamq._check_unread_messages()
        assert warnings != []

    def test_no_warning_when_inbox_empty(self) -> None:
        with patch.object(iamq, "_get", return_value={"messages": []}):
            errors, warnings = iamq._check_unread_messages()
        assert warnings == []

    def test_warning_when_unread_messages_exist(self) -> None:
        msgs = [{"id": "1", "priority": "NORMAL", "subject": "hi"}]
        with patch.object(iamq, "_get", return_value={"messages": msgs}):
            errors, warnings = iamq._check_unread_messages()
        assert warnings != []

    def test_warning_mentions_urgent_count(self) -> None:
        msgs = [
            {"id": "1", "priority": "URGENT"},
            {"id": "2", "priority": "HIGH"},
            {"id": "3", "priority": "NORMAL"},
        ]
        with patch.object(iamq, "_get", return_value={"messages": msgs}):
            errors, warnings = iamq._check_unread_messages()
        assert any("2 high" in w.lower() or "urgent" in w.lower() for w in warnings)

    @pytest.mark.parametrize("priority,is_urgent", [
        ("URGENT", True),
        ("HIGH", True),
        ("NORMAL", False),
        ("LOW", False),
    ])
    def test_urgent_priority_counting(self, priority: str, is_urgent: bool) -> None:
        msgs = [{"id": "1", "priority": priority}]
        with patch.object(iamq, "_get", return_value={"messages": msgs}):
            errors, warnings = iamq._check_unread_messages()
        assert warnings != []
        if is_urgent:
            assert any("1 high" in w.lower() or "urgent" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# _check_peer_agents()
# ---------------------------------------------------------------------------


class TestCheckPeerAgents:
    def test_no_errors_when_unreachable(self) -> None:
        with patch.object(iamq, "_get", return_value=None):
            errors, warnings = iamq._check_peer_agents()
        assert errors == []
        assert warnings == []

    def test_no_errors_with_peers(self, capsys: pytest.CaptureFixture) -> None:
        response = {"agents": [{"id": "other_agent"}, {"id": iamq.AGENT_ID}]}
        with patch.object(iamq, "_get", return_value=response):
            errors, warnings = iamq._check_peer_agents()
        assert errors == []
        out = capsys.readouterr().out
        assert "other_agent" in out

    def test_no_errors_with_empty_peers(self, capsys: pytest.CaptureFixture) -> None:
        response = {"agents": [{"id": iamq.AGENT_ID}]}
        with patch.object(iamq, "_get", return_value=response):
            errors, warnings = iamq._check_peer_agents()
        assert errors == []
        out = capsys.readouterr().out
        assert "No peer" in out


# ---------------------------------------------------------------------------
# run() — full iamq pipeline
# ---------------------------------------------------------------------------


class TestIamqPipelineRun:
    def test_passes_when_reachable(self) -> None:
        clean = ([], [])
        with (
            patch.object(iamq, "_check_reachable", return_value=clean),
            patch.object(iamq, "_check_agent_registered", return_value=clean),
            patch.object(iamq, "_check_unread_messages", return_value=clean),
            patch.object(iamq, "_check_peer_agents", return_value=clean),
        ):
            result = iamq.run()
        assert result.passed is True

    def test_fails_when_iamq_unreachable(self) -> None:
        error = (["IAMQ not reachable"], [])
        clean = ([], [])
        with (
            patch.object(iamq, "_check_reachable", return_value=error),
            patch.object(iamq, "_check_agent_registered", return_value=clean),
            patch.object(iamq, "_check_unread_messages", return_value=clean),
            patch.object(iamq, "_check_peer_agents", return_value=clean),
        ):
            result = iamq.run()
        assert result.passed is False

    def test_passes_with_warnings_only(self) -> None:
        warn = ([], ["minor warning"])
        clean = ([], [])
        with (
            patch.object(iamq, "_check_reachable", return_value=clean),
            patch.object(iamq, "_check_agent_registered", return_value=warn),
            patch.object(iamq, "_check_unread_messages", return_value=clean),
            patch.object(iamq, "_check_peer_agents", return_value=clean),
        ):
            result = iamq.run()
        assert result.passed is True
        assert "minor warning" in result.warnings

    def test_exception_in_check_becomes_warning(self) -> None:
        clean = ([], [])
        with (
            patch.object(iamq, "_check_reachable", side_effect=RuntimeError("boom")),
            patch.object(iamq, "_check_agent_registered", return_value=clean),
            patch.object(iamq, "_check_unread_messages", return_value=clean),
            patch.object(iamq, "_check_peer_agents", return_value=clean),
        ):
            result = iamq.run()
        # Exceptions in iamq pipeline become warnings, not errors
        assert any("boom" in w for w in result.warnings)

    def test_result_name_is_iamq_health(self) -> None:
        clean = ([], [])
        with (
            patch.object(iamq, "_check_reachable", return_value=clean),
            patch.object(iamq, "_check_agent_registered", return_value=clean),
            patch.object(iamq, "_check_unread_messages", return_value=clean),
            patch.object(iamq, "_check_peer_agents", return_value=clean),
        ):
            result = iamq.run()
        assert result.name == "IAMQ Health"
