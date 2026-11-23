# plasma-mcp

MCP server (Python, `mcp` 2.x MCPServer + `dbus-next`) that gives agents structured control of
KDE Plasma 6 (CachyOS, Plasma 6.8, Wayland) through D-Bus and KConfig — no screen-scraping.

## Safety model (build in from day one)
- Every write snapshots the touched `~/.config/*rc` files first (`snapshots.py`); `undo_last` restores.
- Tiers in `~/.config/plasma-mcp.toml`: read / write / dangerous (`policy.py`). Every tool calls `policy.require`.
- Write tools default to `dry_run=True`.
- No synthetic keyboard/mouse input (ydotool/libei/RemoteDesktop portal) in v1.
- Screenshots only via xdg-desktop-portal (user consents). Never `spectacle` desktop grabs.
- KDE Do Not Disturb is deliberately ON on the dev machine — notifications won't show; don't change it.

## Status / roadmap
DONE: get_setting, set_setting (+dry run, snapshot), undo_last, media_status, media_play_pause.
NEXT (v1):
1. Windows: `list_windows`, `focus`, `move_to_desktop`, `tile` — port the KWin-script-over-D-Bus
   pattern from `reference/cmc/automation.py` (script calls back into our own D-Bus object).
2. Notifications: `notify`, `watch_notifications` (org.freedesktop.Notifications).
3. Theming: `apply_theme` via plasma-apply-* (later: reuse KDE Customizer's TOML spec;
   NOTE its repo was not found at ~/Desktop/Dev/kde-customizer on 2026-11-23).
LATER: panels/widgets (plasmashell evaluateScript, `dangerous` tier), clipboard (klipper),
shortcuts (kglobalaccel), event streaming, GNOME backend.

## Run
    uv sync --extra dev && uv run pytest
    claude mcp add plasma -- uv --directory ~/Desktop/Dev/plasma-mcp run plasma-mcp
