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
