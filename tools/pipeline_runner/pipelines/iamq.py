"""IAMQ pipeline — checks inter-agent message queue health and agent registration."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from tools.pipeline_runner.runner import PipelineResult

AGENT_ID = os.environ.get("IAMQ_AGENT_ID", "sysadmin_agent")
IAMQ_BASE_URL = os.environ.get("IAMQ_BASE_URL", "http://127.0.0.1:18790")


def _get(path: str) -> dict | None:
    """GET from IAMQ, return None if unreachable."""
    try:
        req = urllib.request.Request(f"{IAMQ_BASE_URL}{path}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def _check_reachable() -> tuple[list[str], list[str]]:
    """Check if IAMQ service is reachable."""
    result = _get("/status")
    if result is None:
        return [f"IAMQ not reachable at {IAMQ_BASE_URL}"], []
    return [], []


def _check_agent_registered() -> tuple[list[str], list[str]]:
    """Check if sysadmin_agent is registered."""
    result = _get("/agents")
    if result is None:
        return [], ["Cannot check registration — IAMQ unreachable"]
    agent_ids = [a.get("id") for a in result.get("agents", [])]
    if AGENT_ID not in agent_ids:
        return [], [f"{AGENT_ID} is not registered with IAMQ"]
    return [], []


def _check_unread_messages() -> tuple[list[str], list[str]]:
    """Check for unread messages in inbox."""
    result = _get(f"/inbox/{AGENT_ID}?status=unread")
    if result is None:
        return [], ["Cannot check inbox — IAMQ unreachable"]
    messages = result.get("messages", [])
    if messages:
        count = len(messages)
        urgent = sum(1 for m in messages if m.get("priority") in ("URGENT", "HIGH"))
        warning = f"{count} unread message(s)"
        if urgent:
            warning += f" ({urgent} high/urgent priority)"
        return [], [warning]
    return [], []


def _check_peer_agents() -> tuple[list[str], list[str]]:
    """Report on peer agents online."""
    result = _get("/agents")
    if result is None:
        return [], []
    agent_ids = [a.get("id") for a in result.get("agents", []) if a.get("id") != AGENT_ID]
    if agent_ids:
        print(f"         Peers online: {', '.join(agent_ids)}")
    else:
        print("         No peer agents online")
    return [], []


def run() -> PipelineResult:
    """Run all IAMQ health checks."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    checks = [
        ("IAMQ reachable", _check_reachable),
        ("Agent registered", _check_agent_registered),
        ("Unread messages", _check_unread_messages),
        ("Peer agents", _check_peer_agents),
    ]

    for name, check_fn in checks:
        try:
            errs, warns = check_fn()
            all_errors.extend(errs)
            all_warnings.extend(warns)
            status = "FAIL" if errs else ("WARN" if warns else "OK")
            print(f"  [{status:>4}] {name}")
        except Exception as exc:
            all_warnings.append(f"{name}: {exc}")
            print(f"  [WARN] {name}: {exc}")

    return PipelineResult(
        name="IAMQ Health",
        passed=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings,
    )
