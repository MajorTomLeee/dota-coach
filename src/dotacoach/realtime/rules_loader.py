from pathlib import Path
import yaml
from .rule import Rule

def load_rules(path: Path) -> list[Rule]:
    data = yaml.safe_load(path.read_text())
    return [Rule(**r) for r in data["rules"]]
