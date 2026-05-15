import asyncio
import logging
from abc import ABC, abstractmethod
from .engine import Announcement
from .rule import PRIORITY_RANK

log = logging.getLogger(__name__)

class TtsBackend(ABC):
    @abstractmethod
    async def speak(self, text: str) -> None: ...

class FakeBackend(TtsBackend):
    def __init__(self, speak_delay: float = 0.0):
        self.played: list[str] = []
        self.speak_delay = speak_delay

    async def speak(self, text: str) -> None:
        if self.speak_delay:
            await asyncio.sleep(self.speak_delay)
        self.played.append(text)

class Speaker:
    """Single-track TTS player. Critical announcements interrupt lower-priority
    ones currently playing or queued."""

    def __init__(self, backend: TtsBackend):
        self.backend = backend
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._worker: asyncio.Task | None = None
        self._counter = 0
        self._current_priority: int | None = None
        self._current_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass

    async def say(self, ann: Announcement) -> None:
        self._counter += 1
        prio = PRIORITY_RANK[ann.priority]
        # critical 进来时打断当前 housekeeping 播放
        if (
            ann.priority == "critical"
            and self._current_task
            and self._current_priority is not None
            and self._current_priority > 0
        ):
            self._current_task.cancel()
        await self._queue.put((prio, self._counter, ann))

    async def _run(self) -> None:
        while True:
            prio, _, ann = await self._queue.get()
            self._current_priority = prio
            self._current_task = asyncio.create_task(self.backend.speak(ann.text))
            try:
                await self._current_task
            except asyncio.CancelledError:
                log.info("TTS interrupted: %s", ann.text)
            finally:
                self._current_priority = None
                self._current_task = None
