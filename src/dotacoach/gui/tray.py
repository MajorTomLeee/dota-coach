"""系统托盘应用：常驻进程，菜单驱动 GUI 子进程 + 后台 realtime runner。"""
from __future__ import annotations

import asyncio
import logging
import multiprocessing as mp
import os
import threading
from pathlib import Path
from typing import Optional

import pystray
from pystray import MenuItem as Item, Menu

from dotacoach.gui.icon import make_tray_icon

log = logging.getLogger(__name__)


def _home() -> Path:
    return Path(os.environ.get("DOTACOACH_HOME", Path.cwd()))


def _settings_path() -> Path:
    return _home() / "config" / "settings.yaml"


def _spawn_setup() -> None:
    from dotacoach.gui import setup_window
    p = mp.Process(target=setup_window.main, daemon=False)
    p.start()


def _spawn_viewer() -> None:
    from dotacoach.gui import report_window
    p = mp.Process(target=report_window.main, daemon=False)
    p.start()


class TrayApp:
    def __init__(self):
        self.status: str = "idle"  # idle | online | paused | warn
        self.icon: Optional[pystray.Icon] = None
        self._runner_thread: Optional[threading.Thread] = None
        self._runner_loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner_obj = None
        self._paused = False

    # ---- 菜单回调 ----
    def on_settings(self, _icon=None, _item=None) -> None:
        _spawn_setup()

    def on_view_reports(self, _icon=None, _item=None) -> None:
        _spawn_viewer()

    def on_generate_now(self, _icon=None, _item=None) -> None:
        # 在后台线程跑 weekly，避免阻塞 tray
        threading.Thread(target=self._run_weekly_blocking, daemon=True).start()

    def _run_weekly_blocking(self) -> None:
        try:
            from dotacoach.cli import _run_weekly
            from dotacoach.config import load_settings
            settings = load_settings(_settings_path())
            asyncio.run(_run_weekly(settings, since_days=7))
            self._notify("周报告生成完毕，托盘菜单查看")
        except Exception as e:
            self._notify(f"生成失败：{e}")

    def on_pause_resume(self, _icon=None, _item=None) -> None:
        if not self._runner_obj:
            return
        self._paused = not self._paused
        self._runner_obj.engine.set_muted(self._paused)
        self._set_status("paused" if self._paused else "online")
        self._refresh_menu()

    def on_quit(self, _icon=None, _item=None) -> None:
        self._stop_runner()
        if self.icon:
            self.icon.stop()

    # ---- 后台 runner ----
    def _start_runner(self) -> None:
        if not _settings_path().exists():
            self._set_status("warn")
            return
        self._runner_thread = threading.Thread(
            target=self._runner_main, daemon=True)
        self._runner_thread.start()

    def _runner_main(self) -> None:
        try:
            from dotacoach.config import load_settings
            from dotacoach.events import EventBus
            from dotacoach.gsi.server import serve as gsi_serve
            from dotacoach.consolelog.tailer import LogTailer
            from dotacoach.realtime.runner import RealtimeRunner
            from dotacoach.realtime.voice_backends import make_backend
            from dotacoach.paths import find_dota_root, find_console_log
            from dotacoach.db.dao import Database
            from dotacoach.tasks.tracker import TaskTracker
            from dotacoach.scheduler import build_scheduler
            from dotacoach.cli import _run_weekly

            settings = load_settings(_settings_path())
            bus = EventBus()
            backend = make_backend(settings.voice_engine, voice=settings.voice_name)
            db = Database(_home() / "data" / "coach.db"); db.init_schema()
            tracker = TaskTracker(db)

            rules_path = _home() / "config" / "rules.yaml"
            if not rules_path.exists():
                # 仍然允许跑：rules_loader 会抛错；但若用户没拷 rules.yaml，先报错
                self._set_status("warn")
                return

            self._runner_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._runner_loop)
            runner = RealtimeRunner(
                bus, rules_path, backend,
                current_tasks=tracker.get_current_tasks(),
            )
            self._runner_obj = runner

            async def boot():
                await runner.start()
                dota_root = (Path(settings.dota_path) if settings.dota_path
                             else find_dota_root())
                if dota_root:
                    tailer = LogTailer(find_console_log(dota_root), bus)
                    asyncio.create_task(tailer.run())
                # GSI server in another thread
                threading.Thread(
                    target=gsi_serve, args=(bus, settings.gsi_port),
                    daemon=True,
                ).start()
                # 周日凌晨自动跑
                async def weekly_cb():
                    try:
                        await _run_weekly(settings)
                    except Exception as e:
                        log.error("weekly auto-run failed: %s", e)
                sched = build_scheduler(weekly_cb)
                sched.start()
                self._set_status("online")
                self._refresh_menu()
                while True:
                    await asyncio.sleep(3600)

            self._runner_loop.run_until_complete(boot())
        except Exception as e:
            log.exception("runner crashed: %s", e)
            self._set_status("warn")

    def _stop_runner(self) -> None:
        if self._runner_loop and self._runner_loop.is_running():
            self._runner_loop.call_soon_threadsafe(self._runner_loop.stop)

    # ---- 状态 + 菜单 ----
    def _set_status(self, s: str) -> None:
        self.status = s
        if self.icon:
            self.icon.icon = make_tray_icon(s)
            self.icon.title = self._title_for_status()

    def _title_for_status(self) -> str:
        return {
            "idle": "Dota Coach（待命）",
            "online": "Dota Coach（在线）",
            "paused": "Dota Coach（已暂停）",
            "warn": "Dota Coach（需要配置）",
        }.get(self.status, "Dota Coach")

    def _build_menu(self) -> Menu:
        status_label = f"状态：{self._title_for_status()}"
        pause_label = "恢复播报" if self._paused else "暂停播报"
        return Menu(
            Item(status_label, lambda *_: None, enabled=False),
            Menu.SEPARATOR,
            Item("设置...", self.on_settings),
            Item("查看周报告...", self.on_view_reports),
            Item("立即生成本周报告", self.on_generate_now),
            Item(pause_label, self.on_pause_resume,
                 enabled=lambda _: self._runner_obj is not None),
            Menu.SEPARATOR,
            Item("退出", self.on_quit),
        )

    def _refresh_menu(self) -> None:
        if self.icon:
            self.icon.menu = self._build_menu()
            self.icon.update_menu()

    def _notify(self, msg: str) -> None:
        if self.icon and self.icon.HAS_NOTIFICATION:
            self.icon.notify(msg, "Dota Coach")

    # ---- 入口 ----
    def run(self) -> None:
        # 没 settings → 先弹设置窗口
        if not _settings_path().exists():
            _spawn_setup()
            self._set_status("warn")
        else:
            self._start_runner()

        self.icon = pystray.Icon(
            "DotaCoach",
            icon=make_tray_icon(self.status),
            title=self._title_for_status(),
            menu=self._build_menu(),
        )
        self.icon.run()


def main() -> None:
    mp.freeze_support()  # PyInstaller bundle 安全
    logging.basicConfig(level=logging.INFO)
    TrayApp().run()


if __name__ == "__main__":
    main()
