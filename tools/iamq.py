"""Inter-Agent Message Queue (IAMQ) client.

Provides the sysadmin agent with the ability to register, send/receive messages,
and maintain presence via heartbeats with the OpenClaw IAMQ service.

Usage:
    oc-iamq register                    # Register with IAMQ
    oc-iamq heartbeat                   # Send heartbeat
    oc-iamq inbox                       # Check inbox (all messages)
    oc-iamq inbox --unread              # Check inbox (unread only)
    oc-iamq agents                      # List online agents
    oc-iamq status                      # Queue health status
    oc-iamq send <to> <subject> <body>  # Send a message
    oc-iamq broadcast <subject> <body>  # Broadcast to all agents
    oc-iamq ack <message_id>            # Mark message as read
    python -m tools.iamq                # Same as oc-iamq

See: spec/ARCHITECTURE.md for how IAMQ fits into the workspace
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

AGENT_ID = os.environ.get("IAMQ_AGENT_ID", "sysadmin_agent")
IAMQ_BASE_URL = os.environ.get("IAMQ_BASE_URL", "http://127.0.0.1:18790")


def _request(
    method: str,
    path: str,
    data: dict | None = None,
) -> dict:
    """Make an HTTP request to the IAMQ service."""
    url = f"{IAMQ_BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        print(f"ERROR: Cannot reach IAMQ at {url}: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.HTTPError as exc:
        print(f"ERROR: IAMQ returned {exc.code}: {exc.read().decode()}", file=sys.stderr)
        sys.exit(1)


def register() -> dict:
    """Register this agent with IAMQ."""
    result = _request("POST", "/register", {"agent_id": AGENT_ID})
    print(f"Registered as {AGENT_ID}: {result.get('status', 'ok')}")
    return result


def heartbeat() -> dict:
    """Send a heartbeat (auto-registers if not registered)."""
    result = _request("POST", "/heartbeat", {"agent_id": AGENT_ID})
    print(f"Heartbeat sent for {AGENT_ID}")
    return result


def inbox(unread_only: bool = False) -> dict:
    """Fetch inbox messages."""
    path = f"/inbox/{AGENT_ID}"
    if unread_only:
        path += "?status=unread"
    result = _request("GET", path)
    messages = result.get("messages", [])
    if not messages:
        print("Inbox empty.")
        return result

    for msg in messages:
        priority = msg.get("priority", "NORMAL")
        status = msg.get("status", "?")
        from_agent = msg.get("from", "?")
        subject = msg.get("subject", "(no subject)")
        msg_id = msg.get("id", "?")[:8]
        print(f"  [{priority:>6}] [{status:>6}] {from_agent} → {subject}  ({msg_id}…)")

    print(f"\n{len(messages)} message(s)")
    return result


def agents() -> dict:
    """List all online agents."""
    result = _request("GET", "/agents")
    agent_list = result.get("agents", [])
    if not agent_list:
        print("No agents online.")
        return result

    print("Online agents:")
    for agent in agent_list:
        agent_id = agent.get("id", "?")
        marker = " ← you" if agent_id == AGENT_ID else ""
        print(f"  - {agent_id}{marker}")

    print(f"\n{len(agent_list)} agent(s) online")
    return result


def status() -> dict:
    """Get IAMQ queue health status."""
    result = _request("GET", "/status")
    print(json.dumps(result, indent=2))
    return result


def send_message(
    to: str,
    subject: str,
    body: str,
    *,
    priority: str = "NORMAL",
    msg_type: str = "info",
    reply_to: str | None = None,
) -> dict:
    """Send a message to another agent."""
    data: dict = {
        "from": AGENT_ID,
        "to": to,
        "priority": priority,
        "type": msg_type,
        "subject": subject,
        "body": body,
    }
    if reply_to:
        data["replyTo"] = reply_to
    result = _request("POST", "/send", data)
    print(f"Sent to {to}: {subject}")
    return result


def broadcast_message(subject: str, body: str, *, priority: str = "NORMAL") -> dict:
    """Broadcast a message to all agents."""
    return send_message("broadcast", subject, body, priority=priority, msg_type="info")


def ack_message(message_id: str) -> dict:
    """Mark a message as read."""
    result = _request("PATCH", f"/messages/{message_id}", {"status": "read"})
    print(f"Message {message_id[:8]}… marked as read")
    return result


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="oc-iamq",
        description="Inter-Agent Message Queue client for the sysadmin agent.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("register", help="Register with IAMQ")
    sub.add_parser("heartbeat", help="Send heartbeat")

    inbox_p = sub.add_parser("inbox", help="Check inbox")
    inbox_p.add_argument("--unread", action="store_true", help="Show only unread messages")

    sub.add_parser("agents", help="List online agents")
    sub.add_parser("status", help="Queue health status")

    send_p = sub.add_parser("send", help="Send a message")
    send_p.add_argument("to", help="Target agent ID")
    send_p.add_argument("subject", help="Message subject")
    send_p.add_argument("body", help="Message body")
    send_p.add_argument("--priority", default="NORMAL", choices=["URGENT", "HIGH", "NORMAL", "LOW"])
    send_p.add_argument("--type", default="info", dest="msg_type", choices=["request", "response", "info", "error"])
    send_p.add_argument("--reply-to", default=None, help="Message ID to reply to")

    bcast_p = sub.add_parser("broadcast", help="Broadcast to all agents")
    bcast_p.add_argument("subject", help="Message subject")
    bcast_p.add_argument("body", help="Message body")
    bcast_p.add_argument("--priority", default="NORMAL", choices=["URGENT", "HIGH", "NORMAL", "LOW"])

    ack_p = sub.add_parser("ack", help="Mark a message as read")
    ack_p.add_argument("message_id", help="Message UUID")

    args = parser.parse_args(argv)

    match args.command:
        case "register":
            register()
        case "heartbeat":
            heartbeat()
        case "inbox":
            inbox(unread_only=args.unread)
        case "agents":
            agents()
        case "status":
            status()
        case "send":
            send_message(
                args.to, args.subject, args.body,
                priority=args.priority, msg_type=args.msg_type,
                reply_to=args.reply_to,
            )
        case "broadcast":
            broadcast_message(args.subject, args.body, priority=args.priority)
        case "ack":
            ack_message(args.message_id)


if __name__ == "__main__":
    main()
