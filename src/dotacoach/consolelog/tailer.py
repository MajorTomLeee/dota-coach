import asyncio
import logging
from pathlib import Path
from dotacoach.events import EventBus
from .parser import parse_line

log = logging.getLogger(__name__)

class LogTailer:
    def __init__(self, path: Path, bus: EventBus, poll_interval: float = 0.1):
        self.path = path
        self.bus = bus
        self.poll_interval = poll_interval
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    async def run(self) -> None:
        # 从文件末尾开始 tail（避免重放历史）
        with self.path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)
            while not self._stop:
                line = f.readline()
                if not line:
                    await asyncio.sleep(self.poll_interval)
                    continue
                ev = parse_line(line)
                if ev:
                    await self.bus.publish(ev)
