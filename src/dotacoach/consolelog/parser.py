import re
from typing import Optional
from dotacoach.events import Event

# 时间前缀：HH:MM:SS（Dota 自己的格式可能略有差异，按实际抓样调整）
TIME_RE = r"(\d{2}):(\d{2}):(\d{2})"
PATTERNS = [
    (re.compile(rf"^{TIME_RE} (npc_dota_hero_\w+) cast (\w+)$"),
     lambda m: Event(
         type="log.enemy_cast",
         payload={
             "game_time": int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)),
             "hero": m.group(4),
             "ability": m.group(5),
         },
     )),
    (re.compile(rf"^{TIME_RE} (npc_dota_hero_\w+) purchased (item_\w+)$"),
     lambda m: Event(
         type="log.purchase",
         payload={
             "game_time": int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)),
             "hero": m.group(4),
             "item": m.group(5),
         },
     )),
    (re.compile(rf"^{TIME_RE} (npc_dota_hero_\w+) died$"),
     lambda m: Event(
         type="log.death",
         payload={
             "game_time": int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)),
             "hero": m.group(4),
         },
     )),
]

def parse_line(line: str) -> Optional[Event]:
    line = line.strip()
    for regex, builder in PATTERNS:
        m = regex.match(line)
        if m:
            return builder(m)
    return None
