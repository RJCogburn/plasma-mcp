"""MPRIS media players over the session bus."""
from __future__ import annotations

from dbus_next.aio import MessageBus
from dbus_next.errors import InterfaceNotFoundError

from .. import policy

PREFIX = "org.mpris.MediaPlayer2."
PATH = "/org/mpris/MediaPlayer2"


async def _players(bus: MessageBus) -> list[str]:
    intro = await bus.introspect("org.freedesktop.DBus", "/org/freedesktop/DBus")
    dbus = bus.get_proxy_object("org.freedesktop.DBus", "/org/freedesktop/DBus", intro) \
        .get_interface("org.freedesktop.DBus")
    return [n for n in await dbus.call_list_names() if n.startswith(PREFIX)]


async def media_status() -> list[dict]:
    policy.require("read")
    bus = await MessageBus().connect()
    try:
        out = []
        for name in await _players(bus):
            obj = bus.get_proxy_object(name, PATH, await bus.introspect(name, PATH))
            try:
                p = obj.get_interface("org.mpris.MediaPlayer2.Player")
            except InterfaceNotFoundError:
                continue  # some apps register the name without a Player object
            meta = await p.get_metadata()
            out.append({
                "player": name.removeprefix(PREFIX),
                "status": await p.get_playback_status(),
                "title": meta.get("xesam:title").value if "xesam:title" in meta else None,
                "artist": (meta["xesam:artist"].value or [None])[0] if "xesam:artist" in meta else None,
            })
        return out
    finally:
        bus.disconnect()


async def media_play_pause(player: str) -> str:
    policy.require("write")
    bus = await MessageBus().connect()
    try:
        name = PREFIX + player
        obj = bus.get_proxy_object(name, PATH, await bus.introspect(name, PATH))
        await obj.get_interface("org.mpris.MediaPlayer2.Player").call_play_pause()
        return f"toggled {player}"
    finally:
        bus.disconnect()
