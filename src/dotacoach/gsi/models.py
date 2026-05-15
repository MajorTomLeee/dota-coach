from typing import Optional
from pydantic import BaseModel, Field

class Provider(BaseModel):
    name: str
    appid: int
    version: int
    timestamp: int

class Map(BaseModel):
    name: str
    matchid: str
    game_time: int
    clock_time: int
    daytime: bool
    game_state: str
    win_team: str = "none"

class Player(BaseModel):
    steamid: str
    name: str
    activity: str
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0
    gold: int = 0
    gpm: int = 0
    xpm: int = 0
    team_name: str = "radiant"

class Hero(BaseModel):
    id: int
    name: str
    level: int
    alive: bool
    respawn_seconds: int = 0
    buyback_cost: int = 0
    buyback_cooldown: int = 0
    health: int = 0
    max_health: int = 1
    mana: int = 0
    max_mana: int = 1
    smoked: bool = False
    xpos: int = 0
    ypos: int = 0

class Ability(BaseModel):
    name: str
    level: int = 0
    can_cast: bool = False
    cooldown: int = 0
    ultimate: bool = False

class Item(BaseModel):
    name: str
    cooldown: int = 0

class GsiPayload(BaseModel):
    provider: Optional[Provider] = None
    map: Optional[Map] = None
    player: Optional[Player] = None
    hero: Optional[Hero] = None
    abilities: dict[str, Ability] = Field(default_factory=dict)
    items: dict[str, Item] = Field(default_factory=dict)

    def items_list(self) -> list[Item]:
        return [i for i in self.items.values() if i.name != "empty"]

    def has_tp(self) -> bool:
        return any(i.name == "item_tpscroll" for i in self.items_list())

    def in_game(self) -> bool:
        return (
            self.map is not None
            and self.map.game_state == "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"
        )
