import asyncio
import io
import logging
from .voice import TtsBackend

log = logging.getLogger(__name__)

class EdgeTtsBackend(TtsBackend):
    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        self.voice = voice

    async def speak(self, text: str) -> None:
        import edge_tts
        # 流式合成 + sounddevice 播放
        comm = edge_tts.Communicate(text, voice=self.voice)
        audio_data = bytearray()
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        await asyncio.to_thread(self._play_mp3, bytes(audio_data))

    def _play_mp3(self, data: bytes) -> None:
        import miniaudio
        with miniaudio.PlaybackDevice() as device:
            stream = miniaudio.stream_memory(data)
            device.start(stream)
            # 同步等播完
            for _ in stream:
                pass

class Pyttsx3Backend(TtsBackend):
    def __init__(self):
        import pyttsx3
        self._engine = pyttsx3.init()

    async def speak(self, text: str) -> None:
        await asyncio.to_thread(self._speak_blocking, text)

    def _speak_blocking(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()

def make_backend(kind: str, **kwargs) -> TtsBackend:
    if kind == "edge":
        return EdgeTtsBackend(**kwargs)
    if kind == "pyttsx3":
        return Pyttsx3Backend()
    raise ValueError(f"Unknown TTS backend: {kind}")
