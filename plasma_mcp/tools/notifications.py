"""Desktop notifications over org.freedesktop.Notifications.

watch_notifications reads OTHER apps' notifications (chat messages etc.), so it needs the
'private' tier, which is off by default. It uses a D-Bus monitor connection
(org.freedesktop.DBus.Monitoring.BecomeMonitor) that only sees Notify calls.
"""
from __future__ import annotations

import asyncio
import time

from dbus_next import Message, MessageType, Variant
from dbus_next.aio import MessageBus

from .. import policy

SVC = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
URGENCY = {"low": 0, "normal": 1, "critical": 2}


async def _call(bus: MessageBus, member: str, signature: str = "", body=None,
                interface: str = SVC):
    r = await bus.call(Message(destination=SVC, path=PATH, interface=interface, member=member,
                               signature=signature, body=body or []))
    if r.message_type == MessageType.ERROR:
        raise RuntimeError(f"{member}: {r.error_name} {r.body}")
    return r.body


async def notify(summary: str, body: str = "", app_name: str = "plasma-mcp",
                 urgency: str = "normal", timeout_ms: int = -1, icon: str = "") -> int:
    policy.require("write")
    if urgency not in URGENCY:
        raise ValueError(f"urgency must be one of {list(URGENCY)}")
    bus = await MessageBus().connect()
    try:
        hints = {"urgency": Variant("y", URGENCY[urgency])}
        (nid,) = await _call(bus, "Notify", "susssasa{sv}i",
                             [app_name, 0, icon, summary, body, [], hints, timeout_ms])
        return nid
    finally:
        bus.disconnect()


async def close_notification(notification_id: int) -> str:
    policy.require("write")
    bus = await MessageBus().connect()
    try:
        await _call(bus, "CloseNotification", "u", [notification_id])
        return f"closed {notification_id}"
    finally:
        bus.disconnect()


async def notification_status() -> dict:
    policy.require("read")
    bus = await MessageBus().connect()
    try:
        name, vendor, version, spec = await _call(bus, "GetServerInformation")
        (caps,) = await _call(bus, "GetCapabilities")
        try:  # KDE exposes Do Not Disturb as the Inhibited property
            (inh,) = await _call(bus, "Get", "ss", [SVC, "Inhibited"],
                                 interface="org.freedesktop.DBus.Properties")
            inhibited = bool(inh.value)
        except RuntimeError:
            inhibited = None
        from .settings import get_setting  # KDE's scheduled DND end time, if any
        until = get_setting("plasmanotifyrc", "DoNotDisturb", "Until") or None
        return {"server": name, "vendor": vendor, "version": version, "spec": spec,
                "capabilities": caps, "do_not_disturb": inhibited, "dnd_until": until,
                "note": "with do_not_disturb on, only urgency='critical' pops up"}
    finally:
        bus.disconnect()


async def watch_notifications(seconds: float = 10.0, max_count: int = 20,
                              app_filter: str | None = None) -> list[dict]:
    """Collect notifications sent by any app for `seconds` (max 120)."""
    policy.require("private")
    seconds = max(0.5, min(float(seconds), 120.0))
    bus = await MessageBus().connect()
    seen: list[dict] = []
    done = asyncio.Event()
    t0 = time.monotonic()

    def handler(msg: Message):
        if msg.message_type == MessageType.METHOD_CALL and msg.member == "Notify" \
                and msg.interface == SVC and len(msg.body) >= 8:
            app, _rid, _icon, summary, body, _actions, hints, _timeout = msg.body[:8]
            if not app_filter or app_filter.lower() in str(app).lower():
                u = hints.get("urgency")
                seen.append({"t": round(time.monotonic() - t0, 2), "app": app,
                             "summary": summary, "body": body,
                             "urgency": {0: "low", 1: "normal", 2: "critical"}.get(
                                 u.value if u else 1, "normal")})
                if len(seen) >= max_count:
                    done.set()
        return True  # handled: a monitor connection must never send replies

    try:
        rule = f"type='method_call',interface='{SVC}',member='Notify'"
        r = await bus.call(Message(destination="org.freedesktop.DBus", path="/org/freedesktop/DBus",
                                   interface="org.freedesktop.DBus.Monitoring",
                                   member="BecomeMonitor", signature="asu", body=[[rule], 0]))
        if r.message_type == MessageType.ERROR:
            raise RuntimeError(f"BecomeMonitor: {r.error_name} {r.body}")
        bus.add_message_handler(handler)
        try:
            await asyncio.wait_for(done.wait(), seconds)
        except asyncio.TimeoutError:
            pass
        return seen
    finally:
        bus.disconnect()
