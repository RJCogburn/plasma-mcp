"""Theming by wrapping KDE Customizer's `kdec` CLI (~/Desktop/Dev/kde-customizer).

We shell out instead of importing it: kdec owns the theme format and its built
install.sh is the single install path. We add what an agent needs on top:
dry-run-first, snapshots of every rc file the apply can touch, and an undo that
re-skins the live desktop back to what it was.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from .. import policy, snapshots
from .settings import get_setting

# Files plasma-apply-lookandfeel + kdec's install.sh can write.
THEME_FILES = ["kdeglobals", "kwinrc", "plasmarc", "kcminputrc", "ksplashrc", "konsolerc",
               "kscreenlockerrc", "breezerc"]
LAYOUT_FILES = ["plasma-org.kde.plasma.desktop-appletsrc", "plasmashellrc"]


def _kdec() -> str:
    exe = os.environ.get("KDEC") or shutil.which("kdec") or str(Path.home() / ".local/bin/kdec")
    if not Path(exe).exists():
        raise RuntimeError("kdec not found: install KDE Customizer "
                           "(uv tool install --editable ~/Desktop/Dev/kde-customizer)")
    return exe


def _run(*args: str, timeout: int = 300) -> str:
    r = subprocess.run([_kdec(), *args], capture_output=True, text=True, timeout=timeout)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        raise RuntimeError(f"kdec {args[0]} failed ({r.returncode}):\n{out}")
    return out


def _spec(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file() or p.suffix != ".toml":
        raise ValueError(f"not a theme spec (.toml): {p}")
    return str(p)


def current_theme() -> dict:
    policy.require("read")
    return {
        "look_and_feel": get_setting("kdeglobals", "KDE", "LookAndFeelPackage"),
        "color_scheme": get_setting("kdeglobals", "General", "ColorScheme"),
        "plasma_style": get_setting("plasmarc", "Theme", "name"),
        "icons": get_setting("kdeglobals", "Icons", "Theme"),
        "cursor": get_setting("kcminputrc", "Mouse", "cursorTheme"),
    }


def theme_guide() -> str:
    policy.require("read")
    return _run("ai-guide")


def check_theme(spec: str) -> str:
    policy.require("read")
    return _run("check", _spec(spec))


def _reapply_commands(cur: dict) -> list[list[str]]:
    cmds = []
    if cur["color_scheme"]:
        cmds.append(["plasma-apply-colorscheme", cur["color_scheme"]])
    if cur["plasma_style"]:
        cmds.append(["plasma-apply-desktoptheme", cur["plasma_style"]])
    if cur["cursor"]:
        cmds.append(["plasma-apply-cursortheme", cur["cursor"]])
    if cur["icons"] and Path("/usr/lib/plasma-changeicons").exists():
        cmds.append(["/usr/lib/plasma-changeicons", cur["icons"]])
    return cmds


def apply_theme(spec: str, layout: bool = False, dry_run: bool = True) -> str:
    """dry_run -> check + the install script that would run. Otherwise snapshot, then apply."""
    spec = _spec(spec)
    policy.require("dangerous" if layout else "write")
    check = _run("check", spec)
    extra = ["--layout"] if layout else []
    if dry_run:
        script = _run("apply", spec, *extra, "--dry-run")
        return (f"[dry run] current theme: {current_theme()}\n\ncheck:\n{check}\n\n"
                f"would run:\n{script}\n\nCall again with dry_run=false to apply.")
    cur = current_theme()
    files = THEME_FILES + (LAYOUT_FILES if layout else [])
    after = [["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"]]
    if layout:
        after.append(["systemctl", "--user", "restart", "plasma-plasmashell.service"])
    snap = snapshots.take(files, f"apply_theme {Path(spec).name}{' +layout' if layout else ''}",
                          reapply=_reapply_commands(cur), after=after)
    out = _run("apply", spec, *extra)
    return (f"applied {Path(spec).name} (snapshot {snap.name}; previous theme {cur}; "
            f"undo_last reverts{' and restarts plasmashell' if layout else ''})\n\n{out}")
