# plasma-mcp

An MCP server that lets AI agents read and change a KDE Plasma 6 desktop through D-Bus
and KConfig, with dry runs, per-tier permissions and undo for every write.

    claude mcp add plasma -- uv --directory ~/Desktop/Dev/plasma-mcp run plasma-mcp

Status: early. Settings (with undo) and MPRIS media work; windows, notifications and
theming are next. See CLAUDE.md.
