from pathlib import Path
from dotacoach.paths import gsi_cfg_dir

CFG_TEMPLATE = """\
"DotaCoach"
{
    "uri" "http://127.0.0.1:{port}/gsi"
    "timeout" "5.0"
    "buffer" "0.1"
    "throttle" "0.1"
    "heartbeat" "30.0"
    "data"
    {
        "provider" "1"
        "map" "1"
        "player" "1"
        "hero" "1"
        "abilities" "1"
        "items" "1"
    }
}
"""

def write_gsi_cfg(dota_root: Path, port: int = 4000) -> Path:
    cfg_dir = gsi_cfg_dir(dota_root)
    cfg_dir.mkdir(parents=True, exist_ok=True)
    out = cfg_dir / "gamestate_integration_dotacoach.cfg"
    out.write_text(CFG_TEMPLATE.replace("{port}", str(port)))
    return out
