"""Run one-shot KWin scripts and get a JSON result back over D-Bus.

KWin scripts can't return values to the caller of loadScript, so each run:
1. exports a tiny D-Bus object on our own (unique) bus connection,
2. loads a script whose body calls `reply(obj)` -> callDBus(<us>, ..., "Reply", JSON),
3. waits for the reply, then unloads the script.
Pattern ported from reference/cmc/automation.py (QtDBus there, dbus-next here).
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import uuid

from dbus_next import Message, MessageType
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method

IFACE = "org.plasmamcp.Reply"
OBJ_PATH = "/org/plasmamcp/Reply"

PRELUDE = """
function reply(obj) {
  callDBus(%(service)s, %(path)s, %(iface)s, "Reply", JSON.stringify(obj));
}
function winInfo(w) {
  var g = w.frameGeometry;
  return {id: String(w.internalId), caption: String(w.caption || ""),
          app: String(w.resourceClass || ""), pid: w.pid,
          desktops: (w.desktops || []).map(function (d) { return String(d.name); }),
          on_all_desktops: w.onAllDesktops, minimized: w.minimized,
          active: workspace.activeWindow === w,
          geometry: {x: g.x, y: g.y, width: g.width, height: g.height}};
}
function findWindow(id) {
  var ws = workspace.windowList();
  for (var i = 0; i < ws.length; i++) if (String(ws[i].internalId) === id) return ws[i];
  return null;
}
try {
%(body)s
} catch (e) { reply({error: String(e)}); }
"""


class KWinError(RuntimeError):
    pass


class _Endpoint(ServiceInterface):
    def __init__(self, fut: asyncio.Future):
        super().__init__(IFACE)
        self._fut = fut

    @method()
    def Reply(self, payload: "s"):  # noqa: F821 (dbus-next signature annotation)
        if not self._fut.done():
            self._fut.set_result(payload)


async def _kwin_call(bus: MessageBus, member: str, signature: str = "", body=None):
    r = await bus.call(Message(destination="org.kde.KWin", path="/Scripting",
                               interface="org.kde.kwin.Scripting", member=member,
                               signature=signature, body=body or []))
    if r.message_type == MessageType.ERROR:
        raise KWinError(f"KWin {member}: {r.error_name} {r.body}")
    return r.body


async def run(body: str, timeout: float = 5.0) -> dict | list:
    """Run `body` (JS that must call reply(...)) inside KWin; return the parsed reply."""
    bus = await MessageBus().connect()
    fut = asyncio.get_running_loop().create_future()
    bus.export(OBJ_PATH, _Endpoint(fut))
    name = f"plasma_mcp_{uuid.uuid4().hex[:12]}"
    src = PRELUDE % {"service": json.dumps(bus.unique_name), "path": json.dumps(OBJ_PATH),
                     "iface": json.dumps(IFACE), "body": body}
    fd, path = tempfile.mkstemp(prefix=name, suffix=".js")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(src)
        await _kwin_call(bus, "loadScript", "ss", [path, name])
        await _kwin_call(bus, "start")
        try:
            raw = await asyncio.wait_for(fut, timeout)
        except asyncio.TimeoutError:
            raise KWinError("KWin script did not reply (is this a Plasma 6 session?)") from None
    finally:
        try:
            await _kwin_call(bus, "unloadScript", "s", [name])
        except Exception:
            pass
        os.unlink(path)
        bus.disconnect()
    result = json.loads(raw)
    if isinstance(result, dict) and "error" in result:
        raise KWinError(result["error"])
    return result
