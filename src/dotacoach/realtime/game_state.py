import time
from dataclasses import dataclass, field
from typing import Optional
from dotacoach.events import Event
from dotacoach.gsi.models import GsiPayload

# 关键大招的基础 CD（可后续扩展为完整字典）
KEY_ULT_CDS: dict[str, int] = {
    "lion_finger_of_death": 100,
    "lina_laguna_blade": 70,
    "tidehunter_ravage": 150,
    "enigma_black_hole": 180,
    "magnataur_reverse_polarity": 120,
    "faceless_void_chronosphere": 160,
}

# 简单的中文名映射（够 MVP，后续可扩）
HERO_ZH: dict[str, str] = {
    "npc_dota_hero_lion": "莱恩",
    "npc_dota_hero_lina": "莉娜",
    "npc_dota_hero_tidehunter": "潮汐",
    "npc_dota_hero_enigma": "谜团",
    "npc_dota_hero_magnataur": "马格纳斯",
    "npc_dota_hero_faceless_void": "虚空",
}

@dataclass
class GameStateTracker:
    last_payload: Optional[GsiPayload] = None
    enemy_ult_cast_at: dict[str, float] = field(default_factory=dict)
    enemy_ult_ability: dict[str, str] = field(default_factory=dict)
    last_minimap_view_ts: float = field(default_factory=time.monotonic)
    last_event_type: Optional[str] = None
    deaths_seen: list[str] = field(default_factory=list)

    def apply_event(self, ev: Event) -> None:
        self.last_event_type = ev.type
        if ev.type == "gsi.state":
            self.last_payload = ev.payload["payload"]
        elif ev.type == "log.enemy_cast":
            ability = ev.payload["ability"]
            hero = ev.payload["hero"]
            if ability in KEY_ULT_CDS:
                self.enemy_ult_cast_at[hero] = time.monotonic()
                self.enemy_ult_ability[hero] = ability
        elif ev.type == "log.death":
            self.deaths_seen.append(ev.payload["hero"])

    def snapshot(self) -> dict:
        p = self.last_payload
        now = time.monotonic()
        ctx: dict = {
            "now": now,
            "last_minimap_view_ts": self.last_minimap_view_ts,
            "event_just_fired": self.last_event_type,
        }
        if p is not None:
            ctx.update({
                "player": p.player,
                "hero": p.hero,
                "map": p.map,
                "has_tp": p.has_tp(),
                "game_time": p.map.game_time if p.map else 0,
                "level_diff": 0,  # MVP：缺敌方等级数据，留 0；后续可从 OpenDota live 拉
            })
        # 敌方关键大剩余 CD（取最近一次释放的、最即将好的那个）
        enemy_ults: dict[str, float] = {}
        for hero, cast_at in self.enemy_ult_cast_at.items():
            ability = self.enemy_ult_ability[hero]
            cd = KEY_ULT_CDS[ability]
            remaining = cd - (now - cast_at)
            if remaining > 0:
                enemy_ults[hero] = remaining
        ctx["enemy_ults"] = enemy_ults
        if enemy_ults:
            hero, rem = min(enemy_ults.items(), key=lambda kv: kv[1])
            ctx["enemy_key_ult_remaining"] = rem
            ctx["enemy_hero"] = hero
            ctx["enemy_hero_zh"] = HERO_ZH.get(hero, hero)
        else:
            ctx["enemy_key_ult_remaining"] = None
            ctx["enemy_hero"] = None
            ctx["enemy_hero_zh"] = None

        # 缺人估算：30s 内未在 log 中出现且未死 → 视为"missing"
        # MVP：先填 0，留接口
        ctx["missing_enemies_count"] = 0
        ctx["enemies_dead_count"] = 0
        ctx["roshan_alive"] = True
        ctx["next_power_rune_in"] = 9999

        return ctx
