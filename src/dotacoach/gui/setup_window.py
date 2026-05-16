"""设置窗口子进程入口：python -m dotacoach.gui.setup_window"""
from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path

import webview
import yaml

WEB_DIR = Path(__file__).parent / "web"
HTML = WEB_DIR / "setup.html"


def _settings_path() -> Path:
    """优先用环境变量给的工作目录，否则 cwd/config/settings.yaml。"""
    import os
    base = Path(os.environ.get("DOTACOACH_HOME", Path.cwd()))
    return base / "config" / "settings.yaml"


class Api:
    def open_url(self, url: str) -> None:
        webbrowser.open(url)

    def cancel(self) -> None:
        for w in webview.windows:
            w.destroy()

    def load_current(self) -> dict | None:
        p = _settings_path()
        if not p.exists():
            return None
        try:
            return yaml.safe_load(p.read_text())
        except Exception:
            return None

    def save_settings(self, payload: dict) -> dict:
        try:
            steam_id = int(str(payload.get("steam_id_32", "")).strip())
        except ValueError:
            return {"ok": False, "error": "Steam ID 必须是数字"}
        key = (payload.get("anthropic_api_key") or "").strip()
        base_url = (payload.get("anthropic_base_url") or "").strip() or None
        feishu = (payload.get("feishu_webhook_url") or "").strip() or None
        if not key:
            return {"ok": False, "error": "Anthropic API key 不能为空"}

        p = _settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        text = (
            f"steam_id_32: {steam_id}\n"
            f'anthropic_api_key: "{key}"\n'
            + (f'anthropic_base_url: "{base_url}"\n' if base_url
               else "anthropic_base_url: null\n")
            + (f'feishu_webhook_url: "{feishu}"\n' if feishu
               else "feishu_webhook_url: null\n")
            + "dota_path: null\n"
            "gsi_port: 4000\n"
            'log_level: "INFO"\n'
            'voice_engine: "edge"\n'
            'voice_name: "zh-CN-XiaoxiaoNeural"\n'
            'mute_hotkey: "F8"\n'
        )
        p.write_text(text)

        # 顺手帮用户跑一次 install-gsi（最佳努力，失败不阻塞）
        try:
            from dotacoach.config import load_settings
            from dotacoach.paths import find_dota_root
            from dotacoach.install_gsi import write_gsi_cfg

            settings = load_settings(p)
            dota_root = (Path(settings.dota_path) if settings.dota_path
                         else find_dota_root())
            if dota_root:
                write_gsi_cfg(dota_root, port=settings.gsi_port)
        except Exception as e:
            return {"ok": True, "path": str(p),
                    "warn": f"GSI cfg 部署失败：{e}（可手动 dotacoach install-gsi）"}

        return {"ok": True, "path": str(p)}


def main() -> None:
    api = Api()
    webview.create_window(
        "Dota Coach 设置", HTML.as_uri(),
        js_api=api, width=560, height=560, resizable=False,
    )
    webview.start()


if __name__ == "__main__":
    main()
