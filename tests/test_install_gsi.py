from pathlib import Path
from dotacoach.install_gsi import write_gsi_cfg

def test_writes_cfg_to_correct_dir(tmp_path):
    dota_root = tmp_path / "dota 2 beta"
    cfg_dir = dota_root / "game" / "dota" / "cfg" / "gamestate_integration"
    cfg_dir.mkdir(parents=True)
    out = write_gsi_cfg(dota_root, port=4000)
    assert out.exists()
    # Valve GSI cfg key 实际是小写 "uri"，做大小写不敏感断言
    assert "uri" in out.read_text().lower()
    assert "4000" in out.read_text()
