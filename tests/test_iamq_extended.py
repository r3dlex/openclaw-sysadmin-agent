"""Extended tests for tools.iamq — covering untested functions."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from tools import iamq


# ---------------------------------------------------------------------------
# heartbeat()
# ---------------------------------------------------------------------------


class TestHeartbeat:
    def test_returns_result_on_success(self) -> None:
        fake = {"status": "ok"}
        with patch.object(iamq, "_request", return_value=fake):
            result = iamq.heartbeat()
        assert result == fake

    def test_returns_none_on_failure(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.heartbeat()
        assert result is None

    def test_sends_post_to_heartbeat_endpoint(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.heartbeat()
        assert mock_req.call_args[0][0] == "POST"
        assert mock_req.call_args[0][1] == "/heartbeat"

    def test_includes_agent_id_in_payload(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.heartbeat()
        payload = mock_req.call_args[0][2]
        assert "agent_id" in payload


# ---------------------------------------------------------------------------
# inbox()
# ---------------------------------------------------------------------------


class TestInbox:
    def test_returns_none_when_unreachable(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.inbox()
        assert result is None

    def test_returns_result_with_messages(self, capsys: pytest.CaptureFixture) -> None:
        fake = {
            "messages": [
                {"id": "abc12345", "priority": "NORMAL", "status": "unread",
                 "from": "mail_agent", "subject": "Hello"}
            ]
        }
        with patch.object(iamq, "_request", return_value=fake):
            result = iamq.inbox()
        assert result == fake
        out = capsys.readouterr().out
        assert "Hello" in out

    def test_returns_result_with_empty_inbox(self, capsys: pytest.CaptureFixture) -> None:
        fake = {"messages": []}
        with patch.object(iamq, "_request", return_value=fake):
            result = iamq.inbox()
        assert result == fake
        out = capsys.readouterr().out
        assert "empty" in out.lower()

    def test_unread_flag_adds_query_param(self) -> None:
        with patch.object(iamq, "_request", return_value={"messages": []}) as mock_req:
            iamq.inbox(unread_only=True)
        path = mock_req.call_args[0][1]
        assert "unread" in path

    def test_all_messages_without_unread_flag(self) -> None:
        with patch.object(iamq, "_request", return_value={"messages": []}) as mock_req:
            iamq.inbox(unread_only=False)
        path = mock_req.call_args[0][1]
        assert "unread" not in path


# ---------------------------------------------------------------------------
# agents()
# ---------------------------------------------------------------------------


class TestAgents:
    def test_returns_none_when_unreachable(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.agents()
        assert result is None

    def test_returns_result_with_agents(self, capsys: pytest.CaptureFixture) -> None:
        fake = {"agents": [{"id": "mail_agent"}, {"id": iamq.AGENT_ID}]}
        with patch.object(iamq, "_request", return_value=fake):
            result = iamq.agents()
        assert result == fake
        out = capsys.readouterr().out
        assert "mail_agent" in out

    def test_marks_self_in_list(self, capsys: pytest.CaptureFixture) -> None:
        fake = {"agents": [{"id": iamq.AGENT_ID}]}
        with patch.object(iamq, "_request", return_value=fake):
            iamq.agents()
        out = capsys.readouterr().out
        assert "you" in out

    def test_empty_agents_list(self, capsys: pytest.CaptureFixture) -> None:
        fake = {"agents": []}
        with patch.object(iamq, "_request", return_value=fake):
            iamq.agents()
        out = capsys.readouterr().out
        assert "No agents" in out or "0" in out


# ---------------------------------------------------------------------------
# status()
# ---------------------------------------------------------------------------


class TestStatus:
    def test_returns_result_on_success(self, capsys: pytest.CaptureFixture) -> None:
        fake = {"status": "ok", "queue_length": 0}
        with patch.object(iamq, "_request", return_value=fake):
            result = iamq.status()
        assert result == fake
        out = capsys.readouterr().out
        assert "ok" in out

    def test_returns_none_when_unreachable(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.status()
        assert result is None


# ---------------------------------------------------------------------------
# send_message()
# ---------------------------------------------------------------------------


class TestSendMessage:
    def test_returns_result_on_success(self) -> None:
        fake = {"status": "ok"}
        with patch.object(iamq, "_request", return_value=fake):
            result = iamq.send_message("other_agent", "Hello", "World")
        assert result == fake

    def test_returns_none_on_failure(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.send_message("other", "subj", "body")
        assert result is None

    def test_sends_to_correct_endpoint(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.send_message("target", "Subj", "Body")
        assert mock_req.call_args[0][1] == "/send"

    def test_payload_contains_required_fields(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.send_message("agent_x", "Test Subject", "Test Body", priority="HIGH")
        payload = mock_req.call_args[0][2]
        assert payload["to"] == "agent_x"
        assert payload["subject"] == "Test Subject"
        assert payload["body"] == "Test Body"
        assert payload["priority"] == "HIGH"

    def test_reply_to_included_when_set(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.send_message("agent", "subj", "body", reply_to="msg-uuid-123")
        payload = mock_req.call_args[0][2]
        assert payload.get("replyTo") == "msg-uuid-123"

    def test_reply_to_absent_when_not_set(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.send_message("agent", "subj", "body")
        payload = mock_req.call_args[0][2]
        assert "replyTo" not in payload

    @pytest.mark.parametrize("priority", ["URGENT", "HIGH", "NORMAL", "LOW"])
    def test_all_priority_levels(self, priority: str) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.send_message("a", "s", "b", priority=priority)
        payload = mock_req.call_args[0][2]
        assert payload["priority"] == priority


# ---------------------------------------------------------------------------
# broadcast_message()
# ---------------------------------------------------------------------------


class TestBroadcastMessage:
    def test_sends_to_broadcast(self) -> None:
        with patch.object(iamq, "send_message", return_value={"ok": True}) as mock_send:
            iamq.broadcast_message("Alert", "Something happened")
        assert mock_send.call_args[0][0] == "broadcast"

    def test_forwards_priority(self) -> None:
        with patch.object(iamq, "send_message", return_value={"ok": True}) as mock_send:
            iamq.broadcast_message("Alert", "msg", priority="URGENT")
        assert mock_send.call_args[1]["priority"] == "URGENT"


# ---------------------------------------------------------------------------
# ack_message()
# ---------------------------------------------------------------------------


class TestAckMessage:
    def test_patches_correct_endpoint(self) -> None:
        msg_id = "abc-123-def"
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.ack_message(msg_id)
        path = mock_req.call_args[0][1]
        assert msg_id in path
        assert mock_req.call_args[0][0] == "PATCH"

    def test_sets_status_to_read(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.ack_message("id-xyz")
        payload = mock_req.call_args[0][2]
        assert payload["status"] == "read"

    def test_returns_none_on_failure(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.ack_message("id")
        assert result is None


# ---------------------------------------------------------------------------
# acted_message()
# ---------------------------------------------------------------------------


class TestActedMessage:
    def test_sets_status_to_acted(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}) as mock_req:
            iamq.acted_message("id-xyz")
        payload = mock_req.call_args[0][2]
        assert payload["status"] == "acted"

    def test_returns_result_on_success(self) -> None:
        with patch.object(iamq, "_request", return_value={"ok": True}):
            result = iamq.acted_message("msg-id")
        assert result == {"ok": True}

    def test_returns_none_on_failure(self) -> None:
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.acted_message("msg-id")
        assert result is None


# ---------------------------------------------------------------------------
# main() — extended CLI coverage
# ---------------------------------------------------------------------------


class TestMainExtended:
    def test_agents_command_dispatches(self) -> None:
        with patch.object(iamq, "agents") as mock_fn:
            iamq.main(["agents"])
        mock_fn.assert_called_once()

    def test_status_command_dispatches(self) -> None:
        with patch.object(iamq, "status") as mock_fn:
            iamq.main(["status"])
        mock_fn.assert_called_once()

    def test_broadcast_command_dispatches(self) -> None:
        with patch.object(iamq, "broadcast_message") as mock_fn:
            iamq.main(["broadcast", "Subject", "Body"])
        mock_fn.assert_called_once()

    def test_acted_command_dispatches(self) -> None:
        with patch.object(iamq, "acted_message") as mock_fn:
            iamq.main(["acted", "some-uuid"])
        mock_fn.assert_called_once_with("some-uuid")

    def test_send_with_custom_type(self) -> None:
        with patch.object(iamq, "send_message") as mock_fn:
            iamq.main(["send", "agent_x", "Subject", "Body", "--type", "request"])
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args[1]
        assert kwargs["msg_type"] == "request"

    def test_send_with_reply_to(self) -> None:
        with patch.object(iamq, "send_message") as mock_fn:
            iamq.main(["send", "agent_x", "Re: thing", "Body", "--reply-to", "orig-id"])
        kwargs = mock_fn.call_args[1]
        assert kwargs["reply_to"] == "orig-id"

    def test_inbox_without_unread_flag(self) -> None:
        with patch.object(iamq, "inbox") as mock_fn:
            iamq.main(["inbox"])
        mock_fn.assert_called_once_with(unread_only=False)
