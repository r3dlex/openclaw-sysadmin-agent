"""Smoke tests for tools.iamq — IAMQ client for the sysadmin agent."""

from __future__ import annotations

import json
import urllib.error
from http.client import HTTPResponse
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from tools import iamq


# ---------------------------------------------------------------------------
# _request() — low-level HTTP helper
# ---------------------------------------------------------------------------

class TestRequest:
    """Tests for the _request() HTTP helper."""

    def test_returns_none_on_connection_error(self):
        """_request() returns None when the IAMQ service is unreachable."""
        # Use a port that is almost certainly not listening
        with patch.object(iamq, "IAMQ_HTTP_URL", "http://127.0.0.1:1"):
            result = iamq._request("GET", "/status")
        assert result is None

    def test_returns_parsed_json_on_success(self):
        """_request() returns parsed JSON on a successful HTTP response."""
        body = json.dumps({"status": "ok"}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = iamq._request("GET", "/status")

        assert result == {"status": "ok"}

    def test_returns_none_on_http_error(self):
        """_request() returns None on HTTPError (e.g. 404)."""
        exc = urllib.error.HTTPError(
            url="http://example.com",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=BytesIO(b"not found"),
        )
        with patch("urllib.request.urlopen", side_effect=exc):
            result = iamq._request("GET", "/nonexistent")

        assert result is None


# ---------------------------------------------------------------------------
# register() — agent registration
# ---------------------------------------------------------------------------

class TestRegister:
    """Tests for register() with mocked HTTP."""

    def test_register_success(self):
        """register() prints success and returns result dict."""
        fake_response = {"status": "ok", "agent_id": "sysadmin_agent"}

        with patch.object(iamq, "_request", return_value=fake_response) as mock_req:
            result = iamq.register()

        assert result == fake_response
        mock_req.assert_called_once()
        call_args = mock_req.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/register"
        # Verify registration payload contains required fields
        payload = call_args[0][2]
        assert "agent_id" in payload
        assert "capabilities" in payload
        assert isinstance(payload["capabilities"], list)

    def test_register_failure_returns_none(self):
        """register() returns None when IAMQ is unreachable."""
        with patch.object(iamq, "_request", return_value=None):
            result = iamq.register()

        assert result is None


# ---------------------------------------------------------------------------
# main() — CLI argument parsing
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for CLI entry point argument parsing."""

    def test_register_command_dispatches(self):
        """'register' command calls register()."""
        with patch.object(iamq, "register") as mock_fn:
            iamq.main(["register"])
        mock_fn.assert_called_once()

    def test_heartbeat_command_dispatches(self):
        """'heartbeat' command calls heartbeat()."""
        with patch.object(iamq, "heartbeat") as mock_fn:
            iamq.main(["heartbeat"])
        mock_fn.assert_called_once()

    def test_inbox_unread_flag(self):
        """'inbox --unread' passes unread_only=True."""
        with patch.object(iamq, "inbox") as mock_fn:
            iamq.main(["inbox", "--unread"])
        mock_fn.assert_called_once_with(unread_only=True)

    def test_send_command_dispatches(self):
        """'send' command passes to, subject, body arguments."""
        with patch.object(iamq, "send_message") as mock_fn:
            iamq.main(["send", "mail_agent", "Hello", "World"])
        mock_fn.assert_called_once()
        kwargs = mock_fn.call_args
        assert kwargs[1]["priority"] == "NORMAL"

    def test_no_command_exits(self):
        """No subcommand raises SystemExit."""
        with pytest.raises(SystemExit):
            iamq.main([])

    def test_ack_command_dispatches(self):
        """'ack' command calls ack_message() with the message ID."""
        with patch.object(iamq, "ack_message") as mock_fn:
            iamq.main(["ack", "abc-123"])
        mock_fn.assert_called_once_with("abc-123")
