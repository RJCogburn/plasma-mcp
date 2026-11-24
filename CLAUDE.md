# plasma-mcp

MCP server (Python, `mcp` 2.x MCPServer + `dbus-next`) that gives agents structured control of
KDE Plasma 6 (CachyOS, Plasma 6.8, Wayland) through D-Bus and KConfig — no screen-scraping.

## Safety model (build in from day one)
- Every write snapshots the touched `~/.config/*rc` files first (`snapshots.py`); `undo_last` restores.
- Tiers in `~/.config/plasma-mcp.toml`: read / write / dangerous (`policy.py`). Every tool calls `policy.require`.
- Write tools default to `dry_run=True`.
- No synthetic keyboard/mouse input (ydotool/libei/RemoteDesktop portal) in v1.
- Screenshots only via xdg-desktop-portal (user consents). Never `spectacle` desktop grabs.
- Never change the user's Do Not Disturb setting. Test notifications with urgency='low', app_name filter,
  and only watch notifications you sent yourself (filter by app_filter).

## Status / roadmap
DONE: get_setting, set_setting (+dry run, snapshot), undo_last, media_status, media_play_pause,
list_windows, focus_window, move_to_desktop, tile_window (verified live 2026-11-23 on throwaway windows).
`kwin.run(js)` = one-shot KWin script that `reply(obj)`s JSON back to our unique bus name (see kwin.py);
reuse it for any new KWin feature. Geometry after a tile/maximize updates asynchronously — re-read
with list_windows after ~0.5 s. Test write tools on throwaway windows (Tk/kdialog), never the user's own.
Fixed-size dialogs (kdialog --msgbox) ignore tile/maximize.
Theming (tools/theme.py): current_theme, theme_guide, check_theme, apply_theme — shells out to `kdec`
(KDE Customizer). apply snapshots THEME_FILES (+LAYOUT_FILES with layout=True, which needs the
'dangerous' tier) and records reapply commands (plasma-apply-colorscheme/desktoptheme/cursortheme,
/usr/lib/plasma-changeicons) that undo runs BEFORE copying files back, so the live desktop re-skins.
LESSON: theme values usually live in ~/.config/kdedefaults/* (written by plasma-apply-lookandfeel), not the
user rc files — restoring only user rc files leaves the new theme active. Snapshots include kdedefaults/ and
undo first re-applies the previous LnF package (never with --resetLayout).
Live round trip (Midnight -> undo -> Origin600I Light) VERIFIED 2026-11-23: theme + all files byte-identical.
Live apply tests change the user's desktop — ask first.
Notifications (tools/notifications.py): notify, close_notification, notification_status (DND via the
Inhibited property + plasmanotifyrc [DoNotDisturb] Until), watch_notifications (D-Bus BecomeMonitor on
Notify calls; handler must return True so the monitor connection never replies). watch needs the
'private' tier (off by default). Verified live 2026-11-23.
v1 feature set DONE. Next candidates: packaging/README for others, event streaming.
LATER: panels/widgets (plasmashell evaluateScript, `dangerous` tier), clipboard (klipper),
shortcuts (kglobalaccel), event streaming, GNOME backend.

## Run
    uv sync --extra dev && uv run pytest
    claude mcp add plasma -- uv --directory ~/Desktop/Dev/plasma-mcp run plasma-mcp
