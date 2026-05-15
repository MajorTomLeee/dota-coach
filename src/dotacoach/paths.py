import platform
from pathlib import Path
from typing import Optional
import vdf

def _default_steam_root() -> Optional[Path]:
    sys = platform.system()
    if sys == "Darwin":
        return Path.home() / "Library/Application Support/Steam"
    if sys == "Windows":
        for p in [Path("C:/Program Files (x86)/Steam"), Path("C:/Program Files/Steam")]:
            if p.exists():
                return p
    return None

def find_dota_root(steam_root: Optional[Path] = None) -> Optional[Path]:
    root = steam_root or _default_steam_root()
    if not root:
        return None
    libs_file = root / "steamapps" / "libraryfolders.vdf"
    if not libs_file.exists():
        return None
    libs = vdf.loads(libs_file.read_text())
    candidates = []
    for entry in libs.get("libraryfolders", {}).values():
        path = Path(entry["path"]) if isinstance(entry, dict) else Path(entry)
        candidates.append(path / "steamapps" / "common" / "dota 2 beta")
    for c in candidates:
        if c.exists():
            return c
    return None

def find_console_log(dota_root: Path) -> Path:
    return dota_root / "game" / "dota" / "console.log"

def gsi_cfg_dir(dota_root: Path) -> Path:
    return dota_root / "game" / "dota" / "cfg" / "gamestate_integration"
