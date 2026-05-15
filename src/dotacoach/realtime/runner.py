import logging
from pathlib import Path

from dotacoach.events import Event, EventBus
from dotacoach.tasks.linker import boost_rules_for_tasks

from .engine import RuleEngine
from .game_state import GameStateTracker
from .rules_loader import load_rules
from .voice import Speaker, TtsBackend

log = logging.getLogger(__name__)

REALTIME_EVENT_TYPES = (
    "gsi.state",
    "gsi.no_tp",
    "gsi.death",
    "gsi.buyback_ready",
    "log.enemy_cast",
    "log.death",
    "log.purchase",
)


class RealtimeRunner:
    def __init__(
        self,
        bus: EventBus,
        rules_path: Path,
        tts_backend: TtsBackend,
        current_tasks: list[dict] | None = None,
    ):
        self.bus = bus
        self.tracker = GameStateTracker()
        rules = load_rules(rules_path)
        if current_tasks:
            rules = boost_rules_for_tasks(rules, current_tasks)
        self.engine = RuleEngine(rules)
        self.speaker = Speaker(tts_backend)

    async def start(self) -> None:
        await self.speaker.start()
        for t in REALTIME_EVENT_TYPES:
            self.bus.subscribe(t, self._on_event)

    async def stop(self) -> None:
        await self.speaker.stop()

    def toggle_mute(self) -> None:
        self.engine.set_muted(not self.engine._muted)
        log.info("Mute: %s", self.engine._muted)

    async def _on_event(self, ev: Event) -> None:
        self.tracker.apply_event(ev)
        ctx = self.tracker.snapshot()
        for ann in self.engine.evaluate(ctx):
            await self.speaker.say(ann)
