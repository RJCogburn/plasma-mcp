"""KConfig read/write via kreadconfig6 / kwriteconfig6, with dry-run + snapshots."""
from __future__ import annotations

import subprocess

from .. import policy, snapshots


def _group_args(group: str) -> list[str]:
    # "Group/SubGroup" -> --group Group --group SubGroup
    out = []
    for g in group.split("/"):
        out += ["--group", g]
    return out


def get_setting(file: str, group: str, key: str) -> str:
    policy.require("read")
    r = subprocess.run(["kreadconfig6", "--file", file, *_group_args(group), "--key", key],
                       capture_output=True, text=True, check=True)
    return r.stdout.rstrip("\n")


def set_setting(file: str, group: str, key: str, value: str, dry_run: bool = True) -> str:
    policy.require("write")
    old = get_setting(file, group, key)
    if dry_run:
        return f"[dry run] {file} [{group}] {key}: {old!r} -> {value!r}"
    snap = snapshots.take([file], f"set {file} [{group}] {key}")
    subprocess.run(["kwriteconfig6", "--file", file, *_group_args(group), "--key", key, value],
                   check=True)
    return f"{file} [{group}] {key}: {old!r} -> {value!r} (snapshot {snap.name}; undo_last to revert)"


def undo_last() -> str:
    policy.require("write")
    snap = snapshots.latest()
    if not snap:
        return "nothing to undo"
    return "restored: " + ", ".join(snapshots.restore(snap))
