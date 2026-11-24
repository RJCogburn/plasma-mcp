import asyncio

import pytest

from plasma_mcp import policy
from plasma_mcp.tools import notifications


def test_watch_needs_private_tier(monkeypatch):
    monkeypatch.setattr(policy, "tiers", lambda: dict(policy.DEFAULTS))
    with pytest.raises(policy.Denied):
        asyncio.run(notifications.watch_notifications(1))


def test_bad_urgency_rejected():
    with pytest.raises(ValueError):
        asyncio.run(notifications.notify("x", urgency="loud"))


def test_server_registers_notification_tools():
    from plasma_mcp import server
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"notify", "close_notification", "notification_status", "watch_notifications"} <= names
