import os
from pathlib import Path
from click.testing import CliRunner
from dotacoach.cli import main


def test_init_writes_settings_via_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOTACOACH_STEAM_ID", "12345")
    monkeypatch.setenv("DOTACOACH_ANTHROPIC_KEY", "sk-ant-test")
    r = CliRunner().invoke(main, ["init", "--non-interactive"])
    assert r.exit_code == 0
    out = tmp_path / "config" / "settings.yaml"
    assert out.exists()
    text = out.read_text()
    assert "steam_id_32: 12345" in text
    assert "sk-ant-test" in text
    assert "feishu_webhook_url: null" in text


def test_init_with_feishu(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOTACOACH_STEAM_ID", "1")
    monkeypatch.setenv("DOTACOACH_ANTHROPIC_KEY", "k")
    monkeypatch.setenv("DOTACOACH_FEISHU_WEBHOOK", "https://hook.example/x")
    r = CliRunner().invoke(main, ["init", "--non-interactive"])
    assert r.exit_code == 0
    text = (tmp_path / "config" / "settings.yaml").read_text()
    assert 'feishu_webhook_url: "https://hook.example/x"' in text
