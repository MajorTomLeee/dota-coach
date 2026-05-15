from pathlib import Path
from dotacoach.config import load_settings, Settings

def test_load_settings_reads_yaml(tmp_path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("""
steam_id_32: 12345
anthropic_api_key: "sk-test"
feishu_webhook_url: "https://example.com/hook"
dota_path: "/Applications/Dota 2"
gsi_port: 4000
""")
    s = load_settings(cfg)
    assert isinstance(s, Settings)
    assert s.steam_id_32 == 12345
    assert s.gsi_port == 4000

def test_missing_required_field_raises(tmp_path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("steam_id_32: 1\n")
    import pytest
    with pytest.raises(Exception):
        load_settings(cfg)
