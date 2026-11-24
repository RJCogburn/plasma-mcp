# plasma-mcp

An [MCP](https://modelcontextprotocol.io) server that lets AI agents (Claude Code, Codex,
Cursor and other MCP clients) see and control a **KDE Plasma 6** desktop. It works through
KDE's own interfaces (D-Bus, KWin scripting and KConfig) instead of screenshots and
simulated clicks.

Every write can be previewed and undone. Ask your agent to "tile my editor next to the
browser", "switch to a dark theme" or "tell me when the build notification arrives".

## Contents

- [Requirements](#requirements)
- [Install](#install)
- [Tools](#tools)
- [Permissions](#permissions)
- [Undo and snapshots](#undo-and-snapshots)
- [How it works](#how-it-works)
- [Limitations](#limitations)
- [Development](#development)

## Requirements

- KDE Plasma 6 (tested on Plasma 6.8, Wayland, CachyOS)
- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- `kreadconfig6` / `kwriteconfig6` and the `plasma-apply-*` tools, which ship with Plasma
- Optional: [KDE Customizer](https://github.com/RJCogburn/kde-customizer) (`kdec` on your
  `PATH`), required only for the theme tools

## Install

```sh
git clone https://github.com/RJCogburn/plasma-mcp.git
cd plasma-mcp
uv sync
```

Register it with Claude Code for all your projects:

```sh
claude mcp add --scope user plasma -- uv --directory /path/to/plasma-mcp run plasma-mcp
```

Start a new Claude Code session; the tools appear as `mcp__plasma__*`.

For other MCP clients, run the stdio command `uv --directory /path/to/plasma-mcp run plasma-mcp`.

For the theme tools, also install KDE Customizer:

```sh
uv tool install --editable /path/to/kde-customizer
```

## Tools

The tier column refers to the permission tiers described [below](#permissions).

### Settings

| Tool | Tier | What it does |
|---|---|---|
| `get_setting` | read | Read a KConfig value, e.g. `kwinrc` / `Windows` / `FocusPolicy`. Nested groups use `/`. |
| `set_setting` | write | Write a KConfig value. **Dry run by default.** |
| `undo_last` | write | Restore the most recent snapshot (settings or theme). |

### Windows

| Tool | Tier | What it does |
|---|---|---|
| `list_windows` | read | Each window's id, app, title, desktops, geometry and active/minimized state, plus the virtual desktops. |
| `focus_window` | write | Activate a window. It un-minimizes it and switches to its desktop. |
| `move_to_desktop` | write | Move a window to a virtual desktop, by name or 1-based number. |
| `tile_window` | write | Tile it to the `left` / `right` / `top` / `bottom` half, `maximize` or `unmaximize`. |

### Theming (needs KDE Customizer)

| Tool | Tier | What it does |
|---|---|---|
| `current_theme` | read | The global theme, color scheme, Plasma style, icons and cursor in use. |
| `theme_guide` | read | The theme spec format. Agents read this before writing a theme. |
| `check_theme` | read | Validate a `.toml` theme spec (contrast, missing installed themes). |
| `apply_theme` | write | Build and apply a spec. **Dry run by default.** It shows the exact install script. `layout=true` also replaces panels and needs the `dangerous` tier. |

### Notifications

| Tool | Tier | What it does |
|---|---|---|
| `notify` | write | Show a notification (`low` / `normal` / `critical`). Returns its id. |
| `close_notification` | write | Close a notification by id. |
| `notification_status` | read | Server info and whether Do Not Disturb is on. |
| `watch_notifications` | **private** | Collect notifications from *any* app for up to 120 s. |

### Media

| Tool | Tier | What it does |
|---|---|---|
| `media_status` | read | MPRIS players with playback status and the current track. |
| `media_play_pause` | write | Toggle play/pause on a player. |

## Permissions

Tools are grouped into tiers. You choose which tiers are enabled in
`~/.config/plasma-mcp.toml`:

```toml
[tiers]
read = true        # default: on
write = true       # default: on  (every write is previewable and undoable)
dangerous = false  # default: off (e.g. replacing your panel layout)
private = false    # default: off (reading other apps' notifications, e.g. chat messages)
```

When a tool's tier is off, the call fails with an error that names the tier and this file.

## Undo and snapshots

Every real write first copies the config files it can touch to
`~/.local/state/plasma-mcp/snapshots/`. `undo_last` restores the newest snapshot and
deletes it, so repeated calls step further back.

Restoring files alone doesn't change a desktop that's already running, so theme snapshots
also record what was active: global theme, color scheme, Plasma style, cursor and icons.
On undo, plasma-mcp re-applies those first, then copies the files back. A theme change and
its undo leave your config byte-for-byte as it was. This was verified on a live desktop.

Two KDE details matter here:

- A global theme's values live in `~/.config/kdedefaults/`, not in the files you would
  expect. Snapshots include that folder.
- Undoing `apply_theme(layout=true)` also restarts plasmashell to bring back your panels.

## How it works

- **Settings**: `kreadconfig6` / `kwriteconfig6`.
- **Windows**: a KWin script can't return a value to whoever loaded it. So for each call,
  plasma-mcp exports a small D-Bus object, loads a one-shot script that calls back to it
  with JSON (`callDBus`), then unloads the script. See `plasma_mcp/kwin.py`; new KWin
  features can reuse `kwin.run(js)`.
- **Theming**: shells out to KDE Customizer's `kdec` (`check`, `apply`, `ai-guide`) rather
  than importing it, so the theme format and its install script stay in one place.
- **Notifications**: `org.freedesktop.Notifications`. Watching uses a D-Bus monitor
  connection (`BecomeMonitor`) that only matches `Notify` calls.
- **Media**: MPRIS over the session bus.

## Limitations

- **Plasma 6 only.** The KWin scripting API changed between Plasma versions; no GNOME
  backend yet.
- **No synthetic keyboard or mouse input.** On Wayland that needs ydotool, libei or the
  RemoteDesktop portal, and it is out of scope for now.
- **No screenshots yet.** When they come, they will go through xdg-desktop-portal so you
  approve each one.
- **Window geometry updates asynchronously.** After `tile_window`, call `list_windows`
  again about half a second later to see the new size.
- **Fixed-size dialogs** ignore tile and maximize.
- **Do Not Disturb.** While it is on, only `critical` notifications pop up. plasma-mcp never
  changes your Do Not Disturb setting.

## Development

```sh
uv sync --extra dev
uv run pytest
```

- Project notes and conventions for coding agents: `CLAUDE.md`.
- Every new tool must call `policy.require(<tier>)`, and every config write must go
  through `snapshots.take` before changing anything.
- Test write tools on throwaway windows (a Tk or `kdialog` window you open yourself),
  never on the user's own windows.
