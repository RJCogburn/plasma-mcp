"""MCP entry point (stdio). Register with Claude Code:

    claude mcp add plasma -- uv --directory ~/Desktop/Dev/plasma-mcp run plasma-mcp
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .tools import media, settings, windows

mcp = MCPServer("plasma")


@mcp.tool()
def get_setting(file: str, group: str, key: str) -> str:
    """Read a KConfig value, e.g. file='kwinrc', group='Windows', key='FocusPolicy'.
    Nested groups use '/', e.g. 'Containments/1/General'."""
    return settings.get_setting(file, group, key)


@mcp.tool()
def set_setting(file: str, group: str, key: str, value: str, dry_run: bool = True) -> str:
    """Write a KConfig value. Defaults to dry_run=True: show the change first, then call
    again with dry_run=False. Every real write is snapshotted; use undo_last to revert."""
    return settings.set_setting(file, group, key, value, dry_run)


@mcp.tool()
def undo_last() -> str:
    """Restore the config files from the most recent snapshot."""
    return settings.undo_last()


@mcp.tool()
async def media_status() -> list[dict]:
    """List MPRIS media players with playback status and current track."""
    return await media.media_status()


@mcp.tool()
async def media_play_pause(player: str) -> str:
    """Toggle play/pause on a player (name as returned by media_status)."""
    return await media.media_play_pause(player)


@mcp.tool()
async def list_windows() -> dict:
    """List normal windows (id, app, caption, desktops, geometry, active/minimized) plus
    the virtual desktops. Use the `id` with focus / move_to_desktop / tile."""
    return await windows.list_windows()


@mcp.tool()
async def focus_window(window_id: str) -> dict:
    """Activate a window (un-minimizes it and switches to its desktop)."""
    return await windows.focus(window_id)


@mcp.tool()
async def move_to_desktop(window_id: str, desktop: str) -> dict:
    """Move a window to a virtual desktop, given by name or 1-based number."""
    return await windows.move_to_desktop(window_id, desktop)


@mcp.tool()
async def tile_window(window_id: str, mode: str) -> dict:
    """Tile a window: left, right, top, bottom (quick tile halves), maximize, unmaximize.
    Activates the window first."""
    return await windows.tile(window_id, mode)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
