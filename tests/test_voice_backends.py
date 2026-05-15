import sys
import pytest
from dotacoach.realtime.voice_backends import make_backend, EdgeTtsBackend, Pyttsx3Backend

def test_make_edge():
    b = make_backend("edge", voice="zh-CN-XiaoxiaoNeural")
    assert isinstance(b, EdgeTtsBackend)

def test_make_pyttsx3():
    b = make_backend("pyttsx3")
    assert isinstance(b, Pyttsx3Backend)

def test_make_unknown_raises():
    with pytest.raises(ValueError):
        make_backend("unknown")
