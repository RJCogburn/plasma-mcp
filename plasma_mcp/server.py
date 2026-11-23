"""MCP entry point (stdio). Register with Claude Code:

    claude mcp add plasma -- uv --directory ~/Desktop/Dev/plasma-mcp run plasma-mcp
"""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from .tools import media, settings

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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
