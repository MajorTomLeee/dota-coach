"""GUI 模块的基础烟雾测试：能 import + 图标能生成。

不真启 pywebview 或 pystray（CI 无显示）。"""
from PIL import Image


def test_icon_generates_for_all_states():
    from dotacoach.gui.icon import make_tray_icon
    for status in ("idle", "online", "paused", "warn"):
        img = make_tray_icon(status)
        assert isinstance(img, Image.Image)
        assert img.size == (64, 64)


def test_setup_api_save_writes_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("DOTACOACH_HOME", str(tmp_path))
    from dotacoach.gui.setup_window import Api
    api = Api()
    r = api.save_settings({
        "steam_id_32": "12345",
        "anthropic_api_key": "sk-test",
        "feishu_webhook_url": "",
    })
    assert r["ok"] is True
    cfg = tmp_path / "config" / "settings.yaml"
    assert cfg.exists()
    text = cfg.read_text()
    assert "steam_id_32: 12345" in text
    assert "sk-test" in text
    assert "feishu_webhook_url: null" in text


def test_setup_api_rejects_empty_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DOTACOACH_HOME", str(tmp_path))
    from dotacoach.gui.setup_window import Api
    r = Api().save_settings({"steam_id_32": "1", "anthropic_api_key": ""})
    assert r["ok"] is False
    assert "API key" in r["error"]


def test_viewer_api_lists_reports(tmp_path, monkeypatch):
    monkeypatch.setenv("DOTACOACH_HOME", str(tmp_path))
    reports = tmp_path / "data" / "reports"
    reports.mkdir(parents=True)
    (reports / "2026-W20.md").write_text("# hi")
    (reports / "2026-W19.md").write_text("# hi2")
    from dotacoach.gui.report_window import Api
    weeks = Api().list_reports()
    assert weeks == ["2026-W20", "2026-W19"]


def test_viewer_renders_markdown_to_html(tmp_path, monkeypatch):
    monkeypatch.setenv("DOTACOACH_HOME", str(tmp_path))
    reports = tmp_path / "data" / "reports"
    reports.mkdir(parents=True)
    (reports / "2026-W20.md").write_text("# Title\n\n- item1\n- item2\n")
    from dotacoach.gui.report_window import Api
    html = Api().render_report("2026-W20")
    assert "<h1>" in html
    assert "<li>item1</li>" in html
