"""周报告查看器子进程入口：python -m dotacoach.gui.report_window"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path

import markdown as md
import webview

WEB_DIR = Path(__file__).parent / "web"
HTML = WEB_DIR / "viewer.html"


def _home() -> Path:
    return Path(os.environ.get("DOTACOACH_HOME", Path.cwd()))


def _reports_dir() -> Path:
    return _home() / "data" / "reports"


class Api:
    def list_reports(self) -> list[str]:
        d = _reports_dir()
        if not d.exists():
            return []
        return sorted(
            (f.stem for f in d.glob("*.md")),
            reverse=True,
        )

    def render_report(self, week_label: str) -> str:
        f = _reports_dir() / f"{week_label}.md"
        if not f.exists():
            return f"<p>报告不存在：{week_label}</p>"
        return md.markdown(f.read_text(), extensions=["tables", "fenced_code"])

    def generate_now(self) -> dict:
        try:
            from dotacoach.config import load_settings
            from dotacoach.cli import _run_weekly  # noqa: PLC0415

            cfg_path = _home() / "config" / "settings.yaml"
            if not cfg_path.exists():
                return {"ok": False, "error": "未找到 settings.yaml，先去设置"}
            settings = load_settings(cfg_path)
            asyncio.run(_run_weekly(settings, since_days=7))
            return {"ok": True, "week_label": datetime.now().strftime("%Y-W%V")}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def main() -> None:
    api = Api()
    webview.create_window(
        "Dota Coach 周报告", HTML.as_uri(),
        js_api=api, width=920, height=720,
    )
    webview.start()


if __name__ == "__main__":
    main()
