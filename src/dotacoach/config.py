from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field

class Settings(BaseModel):
    steam_id_32: int = Field(..., description="Steam 32-bit account ID")
    anthropic_api_key: str
    anthropic_base_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    dota_path: Optional[str] = None
    gsi_port: int = 4000
    log_level: str = "INFO"
    voice_engine: str = "edge"
    voice_name: str = "zh-CN-XiaoxiaoNeural"
    mute_hotkey: str = "F8"

def load_settings(path: Path) -> Settings:
    data = yaml.safe_load(path.read_text())
    return Settings(**data)
