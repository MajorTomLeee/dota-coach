import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Union

Handler = Union[Callable[["Event"], None], Callable[["Event"], Awaitable[None]]]

@dataclass
class Event:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=lambda: asyncio.get_event_loop().time())

class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subs.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        for h in self._subs.get(event.type, []):
            result = h(event)
            if inspect.isawaitable(result):
                asyncio.create_task(result)
