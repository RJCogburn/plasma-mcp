"""Window management through KWin scripts (Plasma 6 API: workspace.windowList etc.)."""
from __future__ import annotations

import json

from .. import kwin, policy

TILE_JS = {
    "left": "workspace.slotWindowQuickTileLeft();",
    "right": "workspace.slotWindowQuickTileRight();",
    "top": "workspace.slotWindowQuickTileTop();",
    "bottom": "workspace.slotWindowQuickTileBottom();",
    "maximize": "w.setMaximize(true, true);",
    "unmaximize": "w.setMaximize(false, false);",
}


async def list_windows() -> dict:
    policy.require("read")
    return await kwin.run("""
var out = [];
var ws = workspace.windowList();
for (var i = 0; i < ws.length; i++) if (ws[i].normalWindow) out.push(winInfo(ws[i]));
reply({windows: out,
       desktops: workspace.desktops.map(function (d) { return String(d.name); }),
       current_desktop: String(workspace.currentDesktop.name)});
""")


def _with_window(window_id: str, js: str) -> str:
    return f"""
var w = findWindow({json.dumps(window_id)});
if (!w) {{ reply({{error: "no window with id " + {json.dumps(window_id)}}}); }}
else {{ {js} }}
"""


async def focus(window_id: str) -> dict:
    policy.require("write")
    return await kwin.run(_with_window(window_id, """
if (w.minimized) w.minimized = false;
workspace.currentDesktop = w.desktops.length ? w.desktops[0] : workspace.currentDesktop;
workspace.activeWindow = w;
reply(winInfo(w));"""))


async def move_to_desktop(window_id: str, desktop: str) -> dict:
    """`desktop` is a desktop name or a 1-based number."""
    policy.require("write")
    return await kwin.run(_with_window(window_id, f"""
var want = {json.dumps(desktop)}, ds = workspace.desktops, d = null;
for (var i = 0; i < ds.length; i++)
  if (String(ds[i].name) === want || String(i + 1) === want) d = ds[i];
if (!d) reply({{error: "no desktop " + want}});
else {{ w.desktops = [d]; reply(winInfo(w)); }}"""))


async def tile(window_id: str, mode: str) -> dict:
    policy.require("write")
    if mode not in TILE_JS:
        raise ValueError(f"mode must be one of {sorted(TILE_JS)}")
    # Quick-tile slots act on the active window, so activate it first.
    return await kwin.run(_with_window(window_id, f"""
workspace.activeWindow = w;
{TILE_JS[mode]}
reply(winInfo(w));"""))
