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
DONE: get_setting, set_setting (+dry run, snapshot), undo_last, media_status, media_play_pause,
list_windows, focus_window, move_to_desktop, tile_window (verified live 2026-11-23 on throwaway windows).
`kwin.run(js)` = one-shot KWin script that `reply(obj)`s JSON back to our unique bus name (see kwin.py);
reuse it for any new KWin feature. Geometry after a tile/maximize updates asynchronously — re-read
with list_windows after ~0.5 s. Test write tools on throwaway windows (Tk/kdialog), never the user's own.
Fixed-size dialogs (kdialog --msgbox) ignore tile/maximize.
NEXT (v1):
2. Notifications: `notify`, `watch_notifications` (org.freedesktop.Notifications).
3. Theming: `apply_theme` = wrap KDE Customizer (~/Desktop/Dev/kde-customizer, github RJCogburn/kde-customizer):
   `kdec check` / `kdec apply SPEC --dry-run` first, real apply only after; snapshot the rc files it touches.
   `kdec ai-guide` gives agents the spec format. Shell out to `kdec` rather than importing it.
LATER: panels/widgets (plasmashell evaluateScript, `dangerous` tier), clipboard (klipper),
shortcuts (kglobalaccel), event streaming, GNOME backend.

## Run
    uv sync --extra dev && uv run pytest
    claude mcp add plasma -- uv --directory ~/Desktop/Dev/plasma-mcp run plasma-mcp
