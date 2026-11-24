"""Snapshot ~/.config rc files before every write so `undo_last` can restore them."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
STORE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "plasma-mcp" / "snapshots"


def take(files: list[str], reason: str, reapply: list[list[str]] | None = None,
         after: list[list[str]] | None = None) -> Path:
    """Copy `files` (relative to ~/.config). On restore, `reapply` commands run BEFORE the
    files are copied back (so live-reloading tools see a real change and broadcast it),
    `after` commands run once the files are back."""
    snap = STORE / time.strftime("%Y%m%d-%H%M%S") / f"{time.time_ns() % 10**6:06d}"
    snap.mkdir(parents=True)
    manifest = {"reason": reason, "files": {}, "reapply": reapply or [], "after": after or []}
    for name in files:
        src = CONFIG_HOME / name
        manifest["files"][name] = src.exists()
        if src.exists():
            shutil.copy2(src, snap / name.replace("/", "__"))
    (snap / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return snap


def latest() -> Path | None:
    snaps = sorted(STORE.glob("*/*/manifest.json"))
    return snaps[-1].parent if snaps else None


def _run_all(cmds: list[list[str]]) -> list[str]:
    failed = []
    for cmd in cmds:
        try:
            if subprocess.run(cmd, capture_output=True, timeout=60).returncode != 0:
                failed.append(" ".join(cmd))
        except (OSError, subprocess.TimeoutExpired):
            failed.append(" ".join(cmd))
    return failed


def restore(snap: Path) -> list[str]:
    manifest = json.loads((snap / "manifest.json").read_text())
    failed = _run_all(manifest.get("reapply", []))
    restored = []
    for name, existed in manifest["files"].items():
        dst = CONFIG_HOME / name
        if existed:
            shutil.copy2(snap / name.replace("/", "__"), dst)
        elif dst.exists():
            dst.unlink()
        restored.append(name)
    failed += _run_all(manifest.get("after", []))
    shutil.rmtree(snap)
    restored += [f"(command failed: {c})" for c in failed]
    return restored
