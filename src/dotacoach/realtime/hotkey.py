import logging
from typing import Callable
from pynput import keyboard

log = logging.getLogger(__name__)

class HotkeyListener:
    def __init__(self, key_name: str, on_press: Callable[[], None]):
        self.key_name = key_name
        self.on_press = on_press
        self._listener: keyboard.Listener | None = None

    def _handle(self) -> None:
        try:
            self.on_press()
        except Exception as e:
            log.error("hotkey callback error: %s", e)

    def start(self) -> None:
        target = getattr(keyboard.Key, self.key_name.lower(), None)
        if target is None:
            log.warning("Unknown hotkey '%s', mute hotkey disabled", self.key_name)
            return

        def on_press(key):
            if key == target:
                self._handle()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
