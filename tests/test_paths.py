import platform
import pytest
from dotacoach.paths import find_dota_root, find_console_log

def test_find_dota_root_returns_path_or_none(tmp_path, monkeypatch):
    # 用 tmp_path 模拟一个 Steam 安装
    steam = tmp_path / "Steam"
    dota = steam / "steamapps" / "common" / "dota 2 beta"
    dota.mkdir(parents=True)
    (steam / "steamapps" / "libraryfolders.vdf").write_text(
        '"libraryfolders" {\n  "0" {\n    "path" "%s"\n  }\n}' % steam
    )
    p = find_dota_root(steam_root=steam)
    assert p is not None
    assert p.name == "dota 2 beta"

def test_console_log_path():
    from pathlib import Path
    dota = Path("/fake/dota 2 beta")
    log = find_console_log(dota)
    assert log == dota / "game" / "dota" / "console.log"
