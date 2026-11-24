import asyncio

import pytest

from plasma_mcp.tools import windows


def test_window_id_is_json_escaped():
    js = windows._with_window('x"); evil(); ("', "reply(1);")
    assert 'findWindow("x\\"); evil(); (\\"")' in js


def test_tile_rejects_unknown_mode():
    with pytest.raises(ValueError):
        asyncio.run(windows.tile("any", "sideways"))


def test_server_registers_window_tools():
    from plasma_mcp import server
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"list_windows", "focus_window", "move_to_desktop", "tile_window"} <= names
