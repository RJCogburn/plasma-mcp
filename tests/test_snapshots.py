import importlib


def test_snapshot_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    from plasma_mcp import snapshots
    importlib.reload(snapshots)
    (tmp_path / "cfg").mkdir()
    rc = tmp_path / "cfg" / "kwinrc"
    rc.write_text("[Windows]\nFocusPolicy=ClickToFocus\n")
    snapshots.take(["kwinrc", "newrc"], "test")
    rc.write_text("changed")
    (tmp_path / "cfg" / "newrc").write_text("created after snapshot")
    assert set(snapshots.restore(snapshots.latest())) == {"kwinrc", "newrc"}
    assert "ClickToFocus" in rc.read_text()
    assert not (tmp_path / "cfg" / "newrc").exists()
    assert snapshots.latest() is None


def test_restore_runs_reapply_before_files_and_after_last(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    from plasma_mcp import snapshots
    importlib.reload(snapshots)
    (tmp_path / "cfg").mkdir()
    rc, log = tmp_path / "cfg" / "kdeglobals", tmp_path / "log"
    rc.write_text("old")
    snapshots.take(["kdeglobals"], "t",
                   reapply=[["sh", "-c", f"cat {rc} >> {log}; echo >> {log}"]],
                   after=[["sh", "-c", f"cat {rc} >> {log}"], ["false"]])
    rc.write_text("new")
    out = snapshots.restore(snapshots.latest())
    assert log.read_text() == "new\nold"     # reapply saw the pre-restore file, after saw the restored one
    assert "(command failed: false)" in out
