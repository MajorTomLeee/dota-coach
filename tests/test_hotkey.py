from unittest.mock import MagicMock
from dotacoach.realtime.hotkey import HotkeyListener

def test_listener_invokes_callback_on_key():
    cb = MagicMock()
    listener = HotkeyListener(key_name="F8", on_press=cb)
    # 直接调用内部 handler 模拟按键
    listener._handle()
    cb.assert_called_once()
