"""Per-tool permission tiers, read from ~/.config/plasma-mcp.toml.

    [tiers]
    read = true        # list/get tools
    write = true       # settings, theme, notifications (always snapshotted)
    dangerous = false  # anything not undoable (e.g. replacing panels)
    private = false    # reading other apps' content (watch_notifications)
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "plasma-mcp.toml"
DEFAULTS = {"read": True, "write": True, "dangerous": False, "private": False}


class Denied(Exception):
    pass


def tiers() -> dict[str, bool]:
    t = dict(DEFAULTS)
    if CONFIG.exists():
        t.update(tomllib.loads(CONFIG.read_text()).get("tiers", {}))
    return t


def require(tier: str):
    if not tiers().get(tier, False):
        raise Denied(f"tier '{tier}' is disabled in {CONFIG}")
