# Dota Coach 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个跨平台（Mac/Win）的私人 Dota 教练工具：实时层在游戏中通过 GSI + Console log 提供合规决策语音提醒；复盘层每周自动用 OpenDota + Claude 挖掘"赢局 vs 输局"差异并生成训练任务。

**Architecture:** 单进程 Python 应用，5 个独立模块通过 SQLite + 内存事件总线解耦。实时层（GSI 接收 → 规则引擎 → TTS）和复盘层（OpenDota 拉取 → 差异统计 → Claude 综合 → 报告推送）完全独立。任务追踪器把复盘产出的训练任务回灌到实时层规则优先级。

**Tech Stack:** Python 3.11+ / FastAPI（GSI server）/ SQLite / httpx / edge-tts + pyttsx3 / watchdog / anthropic SDK with Prompt Caching / APScheduler / pydantic / pytest / uv

**Spec:** `docs/specs/2026-05-15-dota-coach-design.md`

**Phase 检查点（每阶段结束可独立验证/暂停）：**
- Phase 0：项目骨架可运行 `dotacoach --help`
- Phase 1-5：实时层端到端可用（开 Dota 试玩，能听到中文播报）
- Phase 6-9：复盘层端到端可用（手动跑周报告，能在 markdown 里看到 3 条 pattern）
- Phase 10-12：任务闭环 + 推送 + 自动调度
- Phase 13-14：安装脚本 + 烟雾测试

---

## Phase 0：项目骨架

### Task 0.1：初始化项目

**Files:**
- Create: `pyproject.toml`
- Create: `src/dotacoach/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1：写 pyproject.toml**

```toml
[project]
name = "dotacoach"
version = "0.1.0"
description = "Personal Dota 2 coach: real-time advice + weekly blind-spot analysis"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn>=0.29",
    "httpx>=0.27",
    "pydantic>=2.6",
    "pyyaml>=6.0",
    "edge-tts>=6.1",
    "pyttsx3>=2.90",
    "watchdog>=4.0",
    "anthropic>=0.40",
    "apscheduler>=3.10",
    "vdf>=3.4",
    "scipy>=1.12",
    "click>=8.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
    "freezegun>=1.4",
]

[project.scripts]
dotacoach = "dotacoach.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/dotacoach"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2：写 .gitignore**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
data/coach.db
data/reports/
config/settings.yaml
.DS_Store
```

- [ ] **Step 3：写空 __init__.py**

`src/dotacoach/__init__.py` 内容：
```python
__version__ = "0.1.0"
```

`tests/__init__.py` 留空。

- [ ] **Step 4：写最小 README.md**

```markdown
# Dota Coach

Personal Dota 2 coach. See `docs/specs/2026-05-15-dota-coach-design.md`.
```

- [ ] **Step 5：安装并验证**

```bash
cd /Users/bowie/Projects/dota-coach
uv venv && uv pip install -e ".[dev]"
```

Expected: 依赖全部装好。

- [ ] **Step 6：commit**

```bash
git add pyproject.toml src/ tests/ .gitignore README.md
git commit -m "chore: initialize project skeleton"
```

---

### Task 0.2：配置加载（pydantic settings）

**Files:**
- Create: `src/dotacoach/config.py`
- Create: `config/settings.example.yaml`
- Create: `tests/test_config.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_config.py`：
```python
from pathlib import Path
from dotacoach.config import load_settings, Settings

def test_load_settings_reads_yaml(tmp_path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("""
steam_id_32: 12345
anthropic_api_key: "sk-test"
feishu_webhook_url: "https://example.com/hook"
dota_path: "/Applications/Dota 2"
gsi_port: 4000
""")
    s = load_settings(cfg)
    assert isinstance(s, Settings)
    assert s.steam_id_32 == 12345
    assert s.gsi_port == 4000

def test_missing_required_field_raises(tmp_path):
    cfg = tmp_path / "settings.yaml"
    cfg.write_text("steam_id_32: 1\n")
    import pytest
    with pytest.raises(Exception):
        load_settings(cfg)
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_config.py -v
```
Expected: ImportError（dotacoach.config 不存在）。

- [ ] **Step 3：实现 config.py**

`src/dotacoach/config.py`：
```python
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field

class Settings(BaseModel):
    steam_id_32: int = Field(..., description="Steam 32-bit account ID")
    anthropic_api_key: str
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
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_config.py -v
```
Expected: PASS。

- [ ] **Step 5：写 example yaml**

`config/settings.example.yaml`：
```yaml
# 复制为 settings.yaml 后填入实际值
steam_id_32: 0           # OpenDota 用的 32位 ID
anthropic_api_key: "sk-ant-..."
feishu_webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
dota_path: null          # null 时自动探测
gsi_port: 4000
log_level: "INFO"
voice_engine: "edge"     # edge | pyttsx3
voice_name: "zh-CN-XiaoxiaoNeural"
mute_hotkey: "F8"
```

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/config.py config/settings.example.yaml tests/test_config.py
git commit -m "feat(config): add pydantic settings loader"
```

---

### Task 0.3：SQLite schema 与 DAO 基础

**Files:**
- Create: `src/dotacoach/db/__init__.py`
- Create: `src/dotacoach/db/schema.sql`
- Create: `src/dotacoach/db/dao.py`
- Create: `tests/test_db.py`

- [ ] **Step 1：写 schema.sql**

`src/dotacoach/db/schema.sql`：
```sql
CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    start_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    hero_id INTEGER NOT NULL,
    is_radiant INTEGER NOT NULL,
    win INTEGER NOT NULL,
    game_mode INTEGER NOT NULL,
    lobby_type INTEGER NOT NULL,
    avg_mmr INTEGER,
    raw_json TEXT NOT NULL,
    fetched_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_matches_start ON matches(start_time);

CREATE TABLE IF NOT EXISTS match_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    time_s INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    x INTEGER,
    y INTEGER,
    payload_json TEXT,
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

CREATE INDEX IF NOT EXISTS idx_events_match_time ON match_events(match_id, time_s);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_label TEXT NOT NULL,
    description TEXT NOT NULL,
    metric TEXT NOT NULL,
    target REAL NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('>=', '<=')),
    linked_rule_ids TEXT,
    created_at INTEGER NOT NULL,
    completed INTEGER,
    actual REAL
);

CREATE INDEX IF NOT EXISTS idx_tasks_week ON tasks(week_label);

CREATE TABLE IF NOT EXISTS reports (
    week_label TEXT PRIMARY KEY,
    generated_at INTEGER NOT NULL,
    markdown TEXT NOT NULL
);
```

- [ ] **Step 2：写 fail 测试**

`tests/test_db.py`：
```python
from pathlib import Path
from dotacoach.db.dao import Database

def test_init_creates_tables(tmp_path):
    db = Database(tmp_path / "test.db")
    db.init_schema()
    cur = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    names = [r[0] for r in cur.fetchall()]
    assert "matches" in names
    assert "match_events" in names
    assert "tasks" in names
    assert "reports" in names

def test_insert_and_get_match(tmp_path):
    db = Database(tmp_path / "test.db")
    db.init_schema()
    db.insert_match(
        match_id=1, start_time=100, duration=2000, hero_id=14,
        is_radiant=True, win=True, game_mode=22, lobby_type=7,
        avg_mmr=4500, raw_json='{}', fetched_at=1000,
    )
    rows = db.get_matches_since(0)
    assert len(rows) == 1
    assert rows[0]["match_id"] == 1
```

- [ ] **Step 3：跑测试看 fail**

```bash
uv run pytest tests/test_db.py -v
```
Expected: ImportError。

- [ ] **Step 4：实现 DAO**

`src/dotacoach/db/__init__.py`：
```python
from .dao import Database

__all__ = ["Database"]
```

`src/dotacoach/db/dao.py`：
```python
import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA_FILE = Path(__file__).parent / "schema.sql"

class Database:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA_FILE.read_text())
        self.conn.commit()

    def insert_match(self, **kwargs) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO matches
            (match_id, start_time, duration, hero_id, is_radiant, win,
             game_mode, lobby_type, avg_mmr, raw_json, fetched_at)
            VALUES (:match_id, :start_time, :duration, :hero_id, :is_radiant,
                    :win, :game_mode, :lobby_type, :avg_mmr, :raw_json, :fetched_at)""",
            kwargs,
        )
        self.conn.commit()

    def insert_events(self, match_id: int, events: Iterable[dict]) -> None:
        self.conn.executemany(
            """INSERT INTO match_events
            (match_id, time_s, event_type, x, y, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (match_id, e["time_s"], e["event_type"],
                 e.get("x"), e.get("y"), e.get("payload_json"))
                for e in events
            ],
        )
        self.conn.commit()

    def get_matches_since(self, since_ts: int) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT * FROM matches WHERE start_time >= ? ORDER BY start_time",
            (since_ts,),
        )
        return cur.fetchall()
```

- [ ] **Step 5：跑测试**

```bash
uv run pytest tests/test_db.py -v
```
Expected: PASS。

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/db/ tests/test_db.py
git commit -m "feat(db): add SQLite schema and DAO"
```

---

### Task 0.4：CLI 骨架

**Files:**
- Create: `src/dotacoach/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_cli.py`：
```python
from click.testing import CliRunner
from dotacoach.cli import main

def test_help():
    r = CliRunner().invoke(main, ["--help"])
    assert r.exit_code == 0
    assert "run" in r.output
    assert "weekly" in r.output
    assert "install-gsi" in r.output
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_cli.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 CLI**

`src/dotacoach/cli.py`：
```python
import click

@click.group()
def main():
    """Dota Coach CLI."""

@main.command()
def run():
    """Start the realtime layer (常驻进程)。"""
    click.echo("[stub] realtime not yet implemented")

@main.command()
@click.option("--since-days", default=7, type=int)
def weekly(since_days: int):
    """Trigger the weekly review pipeline."""
    click.echo(f"[stub] weekly with since_days={since_days}")

@main.command("install-gsi")
def install_gsi():
    """Install Valve GSI config to the Dota 2 directory."""
    click.echo("[stub] install-gsi not yet implemented")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_cli.py -v
uv run dotacoach --help
```
Expected: PASS, 三个子命令出现在 help 输出里。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/cli.py tests/test_cli.py
git commit -m "feat(cli): add CLI skeleton with run/weekly/install-gsi"
```

---

### Task 0.5：内存事件总线

**Files:**
- Create: `src/dotacoach/events.py`
- Create: `tests/test_events.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_events.py`：
```python
import asyncio
from dotacoach.events import EventBus, Event

async def test_pub_sub():
    bus = EventBus()
    received = []
    async def handler(e: Event):
        received.append(e)
    bus.subscribe("test", handler)
    await bus.publish(Event(type="test", payload={"x": 1}))
    await asyncio.sleep(0.01)
    assert len(received) == 1
    assert received[0].payload["x"] == 1

async def test_multiple_subscribers():
    bus = EventBus()
    a, b = [], []
    bus.subscribe("e", lambda e: a.append(e))
    bus.subscribe("e", lambda e: b.append(e))
    await bus.publish(Event(type="e", payload={}))
    await asyncio.sleep(0.01)
    assert len(a) == 1 and len(b) == 1
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_events.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现事件总线**

`src/dotacoach/events.py`：
```python
import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Union

Handler = Union[Callable[["Event"], None], Callable[["Event"], Awaitable[None]]]

@dataclass
class Event:
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=lambda: asyncio.get_event_loop().time())

class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subs.setdefault(event_type, []).append(handler)

    async def publish(self, event: Event) -> None:
        for h in self._subs.get(event.type, []):
            result = h(event)
            if inspect.isawaitable(result):
                asyncio.create_task(result)
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_events.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/events.py tests/test_events.py
git commit -m "feat(events): add in-memory async event bus"
```

---

**Phase 0 检查点：** `uv run dotacoach --help` 能看到三个子命令。所有测试 PASS。

---

## Phase 1：GSI 接收器

### Task 1.1：GSI payload pydantic 模型

**Files:**
- Create: `src/dotacoach/gsi/__init__.py`
- Create: `src/dotacoach/gsi/models.py`
- Create: `tests/fixtures/gsi/sample_ingame.json`
- Create: `tests/test_gsi_models.py`

- [ ] **Step 1：准备 fixture**

`tests/fixtures/gsi/sample_ingame.json`（简化的 GSI 真实样本）：
```json
{
  "provider": {"name": "Dota 2", "appid": 570, "version": 47, "timestamp": 1715817600},
  "map": {
    "name": "start", "matchid": "7654321", "game_time": 600,
    "clock_time": 540, "daytime": true, "nightstalker_night": false,
    "game_state": "DOTA_GAMERULES_STATE_GAME_IN_PROGRESS",
    "win_team": "none", "customgamename": "", "ward_purchase_cooldown": 0
  },
  "player": {
    "steamid": "76561198000000000", "name": "tester", "activity": "playing",
    "kills": 3, "deaths": 1, "assists": 5, "last_hits": 80, "denies": 12,
    "kill_streak": 0, "team_name": "radiant", "gold": 1500, "gold_reliable": 200,
    "gold_unreliable": 1300, "gold_from_hero_kills": 600, "gold_from_creep_kills": 1200,
    "gpm": 520, "xpm": 600
  },
  "hero": {
    "id": 14, "name": "npc_dota_hero_pudge", "level": 9, "alive": true,
    "respawn_seconds": 0, "buyback_cost": 800, "buyback_cooldown": 0,
    "health": 1200, "max_health": 1500, "mana": 200, "max_mana": 400,
    "silenced": false, "stunned": false, "disarmed": false, "magicimmune": false,
    "hexed": false, "muted": false, "break": false, "smoked": false,
    "has_debuff": false, "talent_1": false, "talent_2": false,
    "talent_3": false, "talent_4": false, "talent_5": false,
    "talent_6": false, "talent_7": false, "talent_8": false,
    "xpos": 100, "ypos": 200
  },
  "abilities": {
    "ability0": {"name":"pudge_meat_hook","level":3,"can_cast":true,"passive":false,"ability_active":true,"cooldown":0,"ultimate":false},
    "ability1": {"name":"pudge_rot","level":2,"can_cast":true,"passive":false,"ability_active":true,"cooldown":0,"ultimate":false},
    "ability2": {"name":"pudge_flesh_heap","level":1,"can_cast":false,"passive":true,"ability_active":true,"cooldown":0,"ultimate":false},
    "ability3": {"name":"pudge_dismember","level":1,"can_cast":true,"passive":false,"ability_active":true,"cooldown":0,"ultimate":true}
  },
  "items": {
    "slot0": {"name":"item_boots","purchaser":0,"can_cast":false,"cooldown":0,"passive":true},
    "slot1": {"name":"empty"},
    "slot2": {"name":"empty"},
    "slot3": {"name":"empty"},
    "slot4": {"name":"empty"},
    "slot5": {"name":"empty"},
    "stash0": {"name":"empty"},
    "teleport0": {"name":"empty"},
    "neutral0": {"name":"empty"}
  }
}
```

- [ ] **Step 2：写 fail 测试**

`tests/test_gsi_models.py`：
```python
import json
from pathlib import Path
from dotacoach.gsi.models import GsiPayload

FIXTURE = Path(__file__).parent / "fixtures/gsi/sample_ingame.json"

def test_parse_sample_payload():
    p = GsiPayload.model_validate_json(FIXTURE.read_text())
    assert p.map.matchid == "7654321"
    assert p.map.game_time == 600
    assert p.player.gold == 1500
    assert p.hero.id == 14
    assert p.hero.level == 9
    assert "item_boots" in [i.name for i in p.items_list()]

def test_has_tp():
    p = GsiPayload.model_validate_json(FIXTURE.read_text())
    assert p.has_tp() is False
```

- [ ] **Step 3：跑测试看 fail**

```bash
uv run pytest tests/test_gsi_models.py -v
```
Expected: ImportError。

- [ ] **Step 4：实现 models**

`src/dotacoach/gsi/__init__.py`：
```python
from .models import GsiPayload

__all__ = ["GsiPayload"]
```

`src/dotacoach/gsi/models.py`：
```python
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
```

- [ ] **Step 5：跑测试**

```bash
uv run pytest tests/test_gsi_models.py -v
```
Expected: PASS。

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/gsi/ tests/test_gsi_models.py tests/fixtures/gsi/
git commit -m "feat(gsi): add pydantic models for GSI payload"
```

---

### Task 1.2：GSI 事件归一化

**Files:**
- Create: `src/dotacoach/gsi/parser.py`
- Create: `tests/test_gsi_parser.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_gsi_parser.py`：
```python
import json
from pathlib import Path
from dotacoach.gsi.models import GsiPayload
from dotacoach.gsi.parser import diff_to_events

FIXTURE = Path(__file__).parent / "fixtures/gsi/sample_ingame.json"

def test_first_payload_emits_state_event():
    payload = GsiPayload.model_validate_json(FIXTURE.read_text())
    events = diff_to_events(prev=None, curr=payload)
    types = [e.type for e in events]
    assert "gsi.state" in types

def test_no_tp_emits_event():
    payload = GsiPayload.model_validate_json(FIXTURE.read_text())
    events = diff_to_events(prev=None, curr=payload)
    types = [e.type for e in events]
    assert "gsi.no_tp" in types

def test_buyback_ready_event_when_cooldown_hits_zero():
    a = GsiPayload.model_validate_json(FIXTURE.read_text())
    b = GsiPayload.model_validate_json(FIXTURE.read_text())
    a.hero.buyback_cooldown = 5
    b.hero.buyback_cooldown = 0
    events = diff_to_events(prev=a, curr=b)
    assert any(e.type == "gsi.buyback_ready" for e in events)
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_gsi_parser.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 parser**

`src/dotacoach/gsi/parser.py`：
```python
from typing import Optional
from dotacoach.events import Event
from .models import GsiPayload

def diff_to_events(prev: Optional[GsiPayload], curr: GsiPayload) -> list[Event]:
    out: list[Event] = []
    if not curr.in_game():
        return out

    out.append(Event(type="gsi.state", payload={"payload": curr}))

    if curr.player and curr.player.gold >= 50 and not curr.has_tp():
        out.append(Event(
            type="gsi.no_tp",
            payload={"gold": curr.player.gold, "game_time": curr.map.game_time}
        ))

    if (
        prev and prev.hero and curr.hero
        and prev.hero.buyback_cooldown > 0 and curr.hero.buyback_cooldown == 0
        and curr.hero.alive
    ):
        out.append(Event(
            type="gsi.buyback_ready",
            payload={"game_time": curr.map.game_time}
        ))

    if (
        prev and prev.hero and curr.hero
        and prev.hero.alive and not curr.hero.alive
    ):
        out.append(Event(
            type="gsi.death",
            payload={
                "game_time": curr.map.game_time,
                "respawn_seconds": curr.hero.respawn_seconds,
                "x": curr.hero.xpos, "y": curr.hero.ypos,
            }
        ))

    return out
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_gsi_parser.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/gsi/parser.py tests/test_gsi_parser.py
git commit -m "feat(gsi): diff payloads into normalized events"
```

---

### Task 1.3：FastAPI GSI server

**Files:**
- Create: `src/dotacoach/gsi/server.py`
- Create: `tests/test_gsi_server.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_gsi_server.py`：
```python
import json
from pathlib import Path
from fastapi.testclient import TestClient
from dotacoach.gsi.server import build_app
from dotacoach.events import EventBus

FIXTURE = Path(__file__).parent / "fixtures/gsi/sample_ingame.json"

def test_post_payload_publishes_events():
    bus = EventBus()
    received = []
    bus.subscribe("gsi.state", lambda e: received.append(e))
    app = build_app(bus)
    client = TestClient(app)
    r = client.post("/gsi", json=json.loads(FIXTURE.read_text()))
    assert r.status_code == 200
    import asyncio; asyncio.run(asyncio.sleep(0.05))
    assert len(received) >= 1

def test_post_invalid_payload_returns_200():
    bus = EventBus()
    app = build_app(bus)
    client = TestClient(app)
    r = client.post("/gsi", json={"junk": True})
    # Valve 可能发不完整 payload，server 必须不挂
    assert r.status_code == 200
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_gsi_server.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 server**

`src/dotacoach/gsi/server.py`：
```python
import logging
from typing import Optional
from fastapi import FastAPI, Request
from dotacoach.events import EventBus
from .models import GsiPayload
from .parser import diff_to_events

log = logging.getLogger(__name__)

def build_app(bus: EventBus) -> FastAPI:
    app = FastAPI()
    state = {"prev": None}

    @app.post("/gsi")
    async def gsi(request: Request):
        try:
            data = await request.json()
            curr = GsiPayload.model_validate(data)
        except Exception as e:
            log.warning("invalid GSI payload: %s", e)
            return {"ok": True}
        prev: Optional[GsiPayload] = state["prev"]
        for ev in diff_to_events(prev, curr):
            await bus.publish(ev)
        state["prev"] = curr
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app

def serve(bus: EventBus, port: int) -> None:
    import uvicorn
    uvicorn.run(build_app(bus), host="127.0.0.1", port=port, log_level="warning")
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_gsi_server.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/gsi/server.py tests/test_gsi_server.py
git commit -m "feat(gsi): FastAPI server receives GSI payloads"
```

---

**Phase 1 检查点：** GSI server 能接 payload 并发出事件。

---

## Phase 2：Console log 监听

### Task 2.1：跨平台 Steam/Dota 路径探测

**Files:**
- Create: `src/dotacoach/paths.py`
- Create: `tests/test_paths.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_paths.py`：
```python
import platform
import pytest
from dotacoach.paths import find_dota_root, find_console_log

def test_find_dota_root_returns_path_or_none(tmp_path, monkeypatch):
    # 用 tmp_path 模拟一个 Steam 安装
    steam = tmp_path / "Steam"
    dota = steam / "steamapps" / "common" / "dota 2 beta"
    dota.mkdir(parents=True)
    (steam / "steamapps" / "libraryfolders.vdf").write_text(
        '"libraryfolders" {\n  "0" {\n    "path" "%s"\n  }\n}' % steam
    )
    p = find_dota_root(steam_root=steam)
    assert p is not None
    assert p.name == "dota 2 beta"

def test_console_log_path():
    from pathlib import Path
    dota = Path("/fake/dota 2 beta")
    log = find_console_log(dota)
    assert log == dota / "game" / "dota" / "console.log"
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_paths.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 paths**

`src/dotacoach/paths.py`：
```python
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
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_paths.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/paths.py tests/test_paths.py
git commit -m "feat(paths): cross-platform Steam/Dota path discovery"
```

---

### Task 2.2：Console log tail + 事件解析

**Files:**
- Create: `src/dotacoach/consolelog/__init__.py`
- Create: `src/dotacoach/consolelog/parser.py`
- Create: `src/dotacoach/consolelog/tailer.py`
- Create: `tests/test_consolelog_parser.py`
- Create: `tests/test_consolelog_tailer.py`
- Create: `tests/fixtures/consolelog/sample.log`

- [ ] **Step 1：准备 fixture**

`tests/fixtures/consolelog/sample.log`（粘贴典型 Dota 2 console line，简化版）：
```
[2026-05-15 10:00:01] [Steam] STEAM_3:0:123 connected
00:10:23 npc_dota_hero_lina cast item_blink
00:11:45 npc_dota_hero_lion cast lion_finger_of_death
00:12:00 npc_dota_hero_pudge purchased item_tpscroll
00:13:10 npc_dota_hero_pudge died
```

- [ ] **Step 2：写 parser 测试**

`tests/test_consolelog_parser.py`：
```python
from pathlib import Path
from dotacoach.consolelog.parser import parse_line

def test_parse_ability_cast():
    e = parse_line("00:11:45 npc_dota_hero_lion cast lion_finger_of_death")
    assert e is not None
    assert e.type == "log.enemy_cast"
    assert e.payload["hero"] == "npc_dota_hero_lion"
    assert e.payload["ability"] == "lion_finger_of_death"
    assert e.payload["game_time"] == 11 * 60 + 45

def test_parse_purchase():
    e = parse_line("00:12:00 npc_dota_hero_pudge purchased item_tpscroll")
    assert e.type == "log.purchase"
    assert e.payload["item"] == "item_tpscroll"

def test_unrecognized_returns_none():
    assert parse_line("[Steam] random line") is None
```

- [ ] **Step 3：跑测试看 fail**

```bash
uv run pytest tests/test_consolelog_parser.py -v
```
Expected: ImportError。

- [ ] **Step 4：实现 parser**

`src/dotacoach/consolelog/__init__.py` 留空。

`src/dotacoach/consolelog/parser.py`：
```python
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
```

> **NOTE：** Dota 2 console.log 的实际行格式可能与示例略有差异（取决于 cvar 设置）。实际接入时跑一局拿真实 log，调整正则。这里的样本格式是假定 `developer 1` 启用后的常见输出。

- [ ] **Step 5：跑 parser 测试**

```bash
uv run pytest tests/test_consolelog_parser.py -v
```
Expected: PASS。

- [ ] **Step 6：写 tailer 测试**

`tests/test_consolelog_tailer.py`：
```python
import asyncio
from dotacoach.consolelog.tailer import LogTailer
from dotacoach.events import EventBus

async def test_tailer_emits_events_on_append(tmp_path):
    log = tmp_path / "console.log"
    log.write_text("00:00:01 npc_dota_hero_lion cast lion_finger_of_death\n")
    bus = EventBus()
    received = []
    bus.subscribe("log.enemy_cast", lambda e: received.append(e))
    tailer = LogTailer(log, bus)
    task = asyncio.create_task(tailer.run())
    await asyncio.sleep(0.1)
    with log.open("a") as f:
        f.write("00:00:02 npc_dota_hero_pudge died\n")
        f.write("00:00:03 npc_dota_hero_lion cast lion_finger_of_death\n")
    await asyncio.sleep(0.2)
    tailer.stop()
    await task
    assert len(received) >= 1
```

- [ ] **Step 7：跑 tailer 测试看 fail**

```bash
uv run pytest tests/test_consolelog_tailer.py -v
```
Expected: ImportError。

- [ ] **Step 8：实现 tailer**

`src/dotacoach/consolelog/tailer.py`：
```python
import asyncio
import logging
from pathlib import Path
from dotacoach.events import EventBus
from .parser import parse_line

log = logging.getLogger(__name__)

class LogTailer:
    def __init__(self, path: Path, bus: EventBus, poll_interval: float = 0.1):
        self.path = path
        self.bus = bus
        self.poll_interval = poll_interval
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    async def run(self) -> None:
        # 从文件末尾开始 tail（避免重放历史）
        with self.path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)
            while not self._stop:
                line = f.readline()
                if not line:
                    await asyncio.sleep(self.poll_interval)
                    continue
                ev = parse_line(line)
                if ev:
                    await self.bus.publish(ev)
```

- [ ] **Step 9：跑所有 consolelog 测试**

```bash
uv run pytest tests/test_consolelog_parser.py tests/test_consolelog_tailer.py -v
```
Expected: PASS。

- [ ] **Step 10：commit**

```bash
git add src/dotacoach/consolelog/ tests/test_consolelog_parser.py tests/test_consolelog_tailer.py tests/fixtures/consolelog/
git commit -m "feat(consolelog): tail Dota console.log and emit normalized events"
```

---

**Phase 2 检查点：** Console log tailer 在文件追加时能正确抛出事件。

---

## Phase 3：实时规则引擎

### Task 3.1：规则模型与 YAML 加载

**Files:**
- Create: `src/dotacoach/realtime/__init__.py`
- Create: `src/dotacoach/realtime/rule.py`
- Create: `src/dotacoach/realtime/rules_loader.py`
- Create: `config/rules.yaml`
- Create: `tests/test_rules_loader.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_rules_loader.py`：
```python
from pathlib import Path
from dotacoach.realtime.rules_loader import load_rules

def test_load_rules(tmp_path):
    cfg = tmp_path / "rules.yaml"
    cfg.write_text("""
rules:
  - id: no_tp
    category: economy
    priority: critical
    cooldown_s: 60
    when: "player.gold >= 50 and not has_tp"
    say: "买 TP"
  - id: minimap_neglect
    category: map_awareness
    priority: tactical
    cooldown_s: 30
    when: "now - last_minimap_view_ts > 60"
    say: "看小地图"
""")
    rules = load_rules(cfg)
    assert len(rules) == 2
    assert rules[0].id == "no_tp"
    assert rules[0].priority == "critical"
    assert rules[1].cooldown_s == 30
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_rules_loader.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 rule + loader**

`src/dotacoach/realtime/__init__.py` 留空。

`src/dotacoach/realtime/rule.py`：
```python
from typing import Literal
from pydantic import BaseModel

Priority = Literal["critical", "tactical", "housekeeping"]

class Rule(BaseModel):
    id: str
    category: str
    priority: Priority = "tactical"
    cooldown_s: int = 30
    when: str
    say: str
    enabled: bool = True

PRIORITY_RANK = {"critical": 0, "tactical": 1, "housekeeping": 2}
```

`src/dotacoach/realtime/rules_loader.py`：
```python
from pathlib import Path
import yaml
from .rule import Rule

def load_rules(path: Path) -> list[Rule]:
    data = yaml.safe_load(path.read_text())
    return [Rule(**r) for r in data["rules"]]
```

- [ ] **Step 4：写 default rules.yaml**

`config/rules.yaml`：
```yaml
rules:
  - id: no_tp
    category: economy
    priority: critical
    cooldown_s: 60
    when: "player and player.gold >= 50 and not has_tp and game_time > 360"
    say: "买 TP"

  - id: minimap_neglect
    category: map_awareness
    priority: tactical
    cooldown_s: 30
    when: "game_time > 60 and (now - last_minimap_view_ts) > 60"
    say: "看小地图"

  - id: enemies_missing
    category: map_awareness
    priority: tactical
    cooldown_s: 20
    when: "missing_enemies_count >= 2"
    say: "敌方 {missing_enemies_count} 缺，注意"

  - id: power_rune_soon
    category: tempo
    priority: tactical
    cooldown_s: 30
    when: "next_power_rune_in <= 20 and next_power_rune_in > 0"
    say: "20 秒神符"

  - id: roshan_window
    category: tempo
    priority: tactical
    cooldown_s: 60
    when: "roshan_alive and enemies_dead_count >= 2"
    say: "可以打肉山"

  - id: level_disadvantage
    category: judgment
    priority: tactical
    cooldown_s: 60
    when: "level_diff <= -2 and game_time > 600"
    say: "等级落后，回线刷"

  - id: buyback_ready
    category: economy
    priority: housekeeping
    cooldown_s: 300
    when: "event_just_fired == 'gsi.buyback_ready'"
    say: "买活好了"

  - id: enemy_ult_soon
    category: cooldown_tracking
    priority: tactical
    cooldown_s: 0
    when: "enemy_key_ult_remaining is not None and enemy_key_ult_remaining < 15 and enemy_key_ult_remaining > 10"
    say: "{enemy_hero_zh} 大快好了"
```

- [ ] **Step 5：跑测试**

```bash
uv run pytest tests/test_rules_loader.py -v
```
Expected: PASS。

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/realtime/__init__.py src/dotacoach/realtime/rule.py src/dotacoach/realtime/rules_loader.py config/rules.yaml tests/test_rules_loader.py
git commit -m "feat(realtime): rule model and YAML loader with default ruleset"
```

---

### Task 3.2：游戏状态聚合器

**Files:**
- Create: `src/dotacoach/realtime/game_state.py`
- Create: `tests/test_game_state.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_game_state.py`：
```python
import time
from dotacoach.realtime.game_state import GameStateTracker
from dotacoach.events import Event
from dotacoach.gsi.models import GsiPayload, Player, Hero, Map, Item

def make_payload(gold=1500, has_tp=False, alive=True, level=10, game_time=600):
    items = {}
    if has_tp:
        items["slot0"] = Item(name="item_tpscroll")
    return GsiPayload(
        map=Map(name="start", matchid="1", game_time=game_time, clock_time=game_time-60,
                daytime=True, game_state="DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"),
        player=Player(steamid="1", name="t", activity="playing", gold=gold),
        hero=Hero(id=14, name="npc_dota_hero_pudge", level=level, alive=alive),
    )

def test_tracker_updates_from_gsi_state():
    tracker = GameStateTracker()
    p = make_payload(gold=1000)
    tracker.apply_event(Event(type="gsi.state", payload={"payload": p}))
    ctx = tracker.snapshot()
    assert ctx["player"].gold == 1000
    assert ctx["has_tp"] is False
    assert ctx["game_time"] == 600

def test_enemy_ult_remaining_decrements_over_time(monkeypatch):
    tracker = GameStateTracker()
    now = [1000.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])
    tracker.apply_event(Event(
        type="log.enemy_cast",
        payload={"game_time": 0, "hero": "npc_dota_hero_lion",
                 "ability": "lion_finger_of_death"}
    ))
    now[0] += 50
    ctx = tracker.snapshot()
    rem = ctx["enemy_ults"].get("npc_dota_hero_lion")
    # Lion 大默认 CD ~100s（无 aghs）；过 50s 应剩 ~50s
    assert rem is not None
    assert 40 <= rem <= 60
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_game_state.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 tracker**

`src/dotacoach/realtime/game_state.py`：
```python
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
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_game_state.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/realtime/game_state.py tests/test_game_state.py
git commit -m "feat(realtime): game state tracker with enemy ult CD estimation"
```

---

### Task 3.3：规则求值与优先级队列

**Files:**
- Create: `src/dotacoach/realtime/engine.py`
- Create: `tests/test_engine.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_engine.py`：
```python
import time
from dotacoach.realtime.engine import RuleEngine
from dotacoach.realtime.rule import Rule

def make_rule(rid, when, say, priority="tactical", cooldown=30):
    return Rule(id=rid, category="t", priority=priority, cooldown_s=cooldown,
                when=when, say=say)

def test_rule_fires_when_condition_true():
    rule = make_rule("r1", "x > 5", "go")
    engine = RuleEngine([rule])
    out = engine.evaluate({"x": 10})
    assert len(out) == 1
    assert out[0].text == "go"

def test_rule_does_not_fire_when_condition_false():
    rule = make_rule("r1", "x > 5", "go")
    engine = RuleEngine([rule])
    assert engine.evaluate({"x": 1}) == []

def test_cooldown_blocks_repeat(monkeypatch):
    rule = make_rule("r1", "x > 5", "go", cooldown=60)
    engine = RuleEngine([rule])
    now = [1000.0]
    monkeypatch.setattr("time.monotonic", lambda: now[0])
    assert engine.evaluate({"x": 10}) != []
    now[0] += 10
    assert engine.evaluate({"x": 10}) == []
    now[0] += 60
    assert engine.evaluate({"x": 10}) != []

def test_priority_ordering():
    high = make_rule("h", "True", "急", priority="critical")
    low  = make_rule("l", "True", "缓", priority="housekeeping")
    engine = RuleEngine([low, high])
    out = engine.evaluate({})
    assert out[0].text == "急"

def test_say_template_substitutes():
    rule = make_rule("r1", "True", "{name} 大快好了")
    engine = RuleEngine([rule])
    out = engine.evaluate({"name": "莱恩"})
    assert out[0].text == "莱恩 大快好了"
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_engine.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 engine**

`src/dotacoach/realtime/engine.py`：
```python
import time
import logging
from dataclasses import dataclass
from .rule import Rule, PRIORITY_RANK

log = logging.getLogger(__name__)

@dataclass
class Announcement:
    rule_id: str
    text: str
    priority: str

class RuleEngine:
    """Evaluates rules against a context dict and emits announcements
    sorted by priority. Per-rule cooldown enforced via monotonic clock."""

    def __init__(self, rules: list[Rule]):
        self.rules = rules
        self.last_fired_at: dict[str, float] = {}

    def evaluate(self, ctx: dict) -> list[Announcement]:
        now = time.monotonic()
        out: list[Announcement] = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            last = self.last_fired_at.get(rule.id)
            if last is not None and (now - last) < rule.cooldown_s:
                continue
            try:
                ok = bool(eval(rule.when, {"__builtins__": {}}, ctx))
            except Exception as e:
                log.debug("rule %s eval failed: %s", rule.id, e)
                continue
            if not ok:
                continue
            try:
                text = rule.say.format(**ctx)
            except Exception:
                text = rule.say
            out.append(Announcement(rule_id=rule.id, text=text, priority=rule.priority))
            self.last_fired_at[rule.id] = now
        out.sort(key=lambda a: PRIORITY_RANK[a.priority])
        return out
```

> **NOTE：** `eval` 在受限作用域里用，规则文件不接受用户输入（只来自我们自己写的 yaml），可以接受。如果以后规则可热更/外部分发，要换 simpleeval 或 ast 白名单。

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_engine.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/realtime/engine.py tests/test_engine.py
git commit -m "feat(realtime): rule engine with cooldown and priority"
```

---

### Task 3.4：战斗静默与全局 mute

**Files:**
- Modify: `src/dotacoach/realtime/engine.py`
- Create: `tests/test_engine_mute.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_engine_mute.py`：
```python
from dotacoach.realtime.engine import RuleEngine
from dotacoach.realtime.rule import Rule

def make(rid, prio="tactical"):
    return Rule(id=rid, category="t", priority=prio, cooldown_s=0,
                when="True", say="x")

def test_global_mute_blocks_all():
    engine = RuleEngine([make("r1")])
    engine.set_muted(True)
    assert engine.evaluate({}) == []
    engine.set_muted(False)
    assert engine.evaluate({}) != []

def test_combat_silence_blocks_non_critical():
    engine = RuleEngine([make("low", "tactical"), make("high", "critical")])
    engine.set_in_combat(True)
    out = engine.evaluate({})
    ids = [a.rule_id for a in out]
    assert "low" not in ids
    assert "high" in ids
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_engine_mute.py -v
```
Expected: AttributeError。

- [ ] **Step 3：扩展 engine**

修改 `src/dotacoach/realtime/engine.py` 的 `RuleEngine` 类，加入：

```python
class RuleEngine:
    def __init__(self, rules: list[Rule]):
        self.rules = rules
        self.last_fired_at: dict[str, float] = {}
        self._muted = False
        self._in_combat = False

    def set_muted(self, muted: bool) -> None:
        self._muted = muted

    def set_in_combat(self, in_combat: bool) -> None:
        self._in_combat = in_combat

    def evaluate(self, ctx: dict) -> list[Announcement]:
        if self._muted:
            return []
        now = time.monotonic()
        out: list[Announcement] = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if self._in_combat and rule.priority != "critical":
                continue
            # ... 其余逻辑保持原样
```

把上面的 `_muted` / `_in_combat` 检查融入 `evaluate`。

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_engine.py tests/test_engine_mute.py -v
```
Expected: 全 PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/realtime/engine.py tests/test_engine_mute.py
git commit -m "feat(realtime): mute toggle and combat silence"
```

---

**Phase 3 检查点：** 给定 ctx 字典，规则引擎能正确产出/抑制 announcement。

---

## Phase 4：TTS 语音

### Task 4.1：TTS 抽象与队列

**Files:**
- Create: `src/dotacoach/realtime/voice.py`
- Create: `tests/test_voice.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_voice.py`：
```python
import asyncio
from dotacoach.realtime.voice import Speaker, FakeBackend
from dotacoach.realtime.engine import Announcement

async def test_speaker_plays_via_backend():
    backend = FakeBackend()
    speaker = Speaker(backend)
    await speaker.start()
    await speaker.say(Announcement(rule_id="r", text="买 TP", priority="critical"))
    await asyncio.sleep(0.05)
    await speaker.stop()
    assert backend.played == ["买 TP"]

async def test_critical_interrupts_low():
    backend = FakeBackend(speak_delay=0.2)
    speaker = Speaker(backend)
    await speaker.start()
    await speaker.say(Announcement(rule_id="a", text="缓", priority="housekeeping"))
    await asyncio.sleep(0.05)
    await speaker.say(Announcement(rule_id="b", text="急", priority="critical"))
    await asyncio.sleep(0.5)
    await speaker.stop()
    assert "急" in backend.played
    # 低优可能被打断或丢弃，重点是 critical 一定播放
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_voice.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 voice**

`src/dotacoach/realtime/voice.py`：
```python
import asyncio
import logging
from abc import ABC, abstractmethod
from .engine import Announcement
from .rule import PRIORITY_RANK

log = logging.getLogger(__name__)

class TtsBackend(ABC):
    @abstractmethod
    async def speak(self, text: str) -> None: ...

class FakeBackend(TtsBackend):
    def __init__(self, speak_delay: float = 0.0):
        self.played: list[str] = []
        self.speak_delay = speak_delay

    async def speak(self, text: str) -> None:
        if self.speak_delay:
            await asyncio.sleep(self.speak_delay)
        self.played.append(text)

class Speaker:
    """Single-track TTS player. Critical announcements interrupt lower-priority
    ones currently playing or queued."""

    def __init__(self, backend: TtsBackend):
        self.backend = backend
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._worker: asyncio.Task | None = None
        self._counter = 0
        self._current_priority: int | None = None
        self._current_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass

    async def say(self, ann: Announcement) -> None:
        self._counter += 1
        prio = PRIORITY_RANK[ann.priority]
        # critical 进来时打断当前 housekeeping 播放
        if (
            ann.priority == "critical"
            and self._current_task
            and self._current_priority is not None
            and self._current_priority > 0
        ):
            self._current_task.cancel()
        await self._queue.put((prio, self._counter, ann))

    async def _run(self) -> None:
        while True:
            prio, _, ann = await self._queue.get()
            self._current_priority = prio
            self._current_task = asyncio.create_task(self.backend.speak(ann.text))
            try:
                await self._current_task
            except asyncio.CancelledError:
                log.info("TTS interrupted: %s", ann.text)
            finally:
                self._current_priority = None
                self._current_task = None
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_voice.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/realtime/voice.py tests/test_voice.py
git commit -m "feat(voice): TTS speaker abstraction with priority interruption"
```

---

### Task 4.2：edge-tts 与 pyttsx3 后端

**Files:**
- Create: `src/dotacoach/realtime/voice_backends.py`
- Create: `tests/test_voice_backends.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_voice_backends.py`：
```python
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
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_voice_backends.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现后端**

`src/dotacoach/realtime/voice_backends.py`：
```python
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
```

> **NOTE：** edge-tts 播放需要 `miniaudio` 解码 mp3。先把它加到 `pyproject.toml` deps：

修改 `pyproject.toml` dependencies，加一行：
```toml
    "miniaudio>=1.59",
```

然后重装：
```bash
uv pip install -e ".[dev]"
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_voice_backends.py -v
```
Expected: PASS（仅工厂方法测试，不实际播放）。

- [ ] **Step 5：手动验证（一次性）**

```bash
uv run python -c "
import asyncio
from dotacoach.realtime.voice_backends import make_backend
asyncio.run(make_backend('edge').speak('Dota Coach 测试播报'))
"
```
Expected: 听到中文女声"Dota Coach 测试播报"。如果没听到，检查音频输出。

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/realtime/voice_backends.py tests/test_voice_backends.py pyproject.toml
git commit -m "feat(voice): edge-tts and pyttsx3 backends"
```

---

### Task 4.3：全局 mute 热键

**Files:**
- Create: `src/dotacoach/realtime/hotkey.py`
- Create: `tests/test_hotkey.py`

- [ ] **Step 1：加依赖**

修改 `pyproject.toml` 加：
```toml
    "pynput>=1.7",
```

```bash
uv pip install -e ".[dev]"
```

- [ ] **Step 2：写 fail 测试**

`tests/test_hotkey.py`：
```python
from unittest.mock import MagicMock
from dotacoach.realtime.hotkey import HotkeyListener

def test_listener_invokes_callback_on_key():
    cb = MagicMock()
    listener = HotkeyListener(key_name="F8", on_press=cb)
    # 直接调用内部 handler 模拟按键
    listener._handle()
    cb.assert_called_once()
```

- [ ] **Step 3：跑测试看 fail**

```bash
uv run pytest tests/test_hotkey.py -v
```
Expected: ImportError。

- [ ] **Step 4：实现 hotkey**

`src/dotacoach/realtime/hotkey.py`：
```python
import logging
from typing import Callable
from pynput import keyboard

log = logging.getLogger(__name__)

class HotkeyListener:
    def __init__(self, key_name: str, on_press: Callable[[], None]):
        self.key_name = key_name
        self.on_press = on_press
        self._listener: keyboard.Listener | None = None

    def _handle(self) -> None:
        try:
            self.on_press()
        except Exception as e:
            log.error("hotkey callback error: %s", e)

    def start(self) -> None:
        target = getattr(keyboard.Key, self.key_name.lower(), None)
        if target is None:
            log.warning("Unknown hotkey '%s', mute hotkey disabled", self.key_name)
            return

        def on_press(key):
            if key == target:
                self._handle()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
```

- [ ] **Step 5：跑测试**

```bash
uv run pytest tests/test_hotkey.py -v
```
Expected: PASS。

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/realtime/hotkey.py tests/test_hotkey.py pyproject.toml
git commit -m "feat(realtime): global mute hotkey via pynput"
```

---

**Phase 4 检查点：** 手动跑能听到 edge-tts 播报中文。

---

## Phase 5：实时层组装

### Task 5.1：实时层启动器（wire-up）

**Files:**
- Create: `src/dotacoach/realtime/runner.py`
- Modify: `src/dotacoach/cli.py`
- Create: `tests/test_realtime_runner.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_realtime_runner.py`：
```python
import asyncio
from pathlib import Path
from dotacoach.realtime.runner import RealtimeRunner
from dotacoach.realtime.voice import FakeBackend
from dotacoach.events import EventBus, Event
from dotacoach.gsi.models import GsiPayload, Player, Hero, Map

async def test_runner_publishes_announcement_on_no_tp(tmp_path):
    bus = EventBus()
    backend = FakeBackend()
    rules_yaml = tmp_path / "rules.yaml"
    rules_yaml.write_text("""
rules:
  - id: no_tp
    category: economy
    priority: critical
    cooldown_s: 0
    when: "player and player.gold >= 50 and not has_tp and game_time > 0"
    say: "买 TP"
""")
    runner = RealtimeRunner(bus, rules_yaml, backend)
    await runner.start()
    p = GsiPayload(
        map=Map(name="x", matchid="1", game_time=600, clock_time=540,
                daytime=True, game_state="DOTA_GAMERULES_STATE_GAME_IN_PROGRESS"),
        player=Player(steamid="1", name="t", activity="playing", gold=1000),
        hero=Hero(id=14, name="npc_dota_hero_pudge", level=5, alive=True),
    )
    await bus.publish(Event(type="gsi.state", payload={"payload": p}))
    await asyncio.sleep(0.1)
    await runner.stop()
    assert "买 TP" in backend.played
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_realtime_runner.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 runner**

`src/dotacoach/realtime/runner.py`：
```python
import logging
from pathlib import Path
from dotacoach.events import EventBus, Event
from .engine import RuleEngine
from .game_state import GameStateTracker
from .rules_loader import load_rules
from .voice import Speaker, TtsBackend

log = logging.getLogger(__name__)

REALTIME_EVENT_TYPES = ("gsi.state", "gsi.no_tp", "gsi.death",
                        "gsi.buyback_ready", "log.enemy_cast", "log.death",
                        "log.purchase")

class RealtimeRunner:
    def __init__(self, bus: EventBus, rules_path: Path, tts_backend: TtsBackend):
        self.bus = bus
        self.tracker = GameStateTracker()
        self.engine = RuleEngine(load_rules(rules_path))
        self.speaker = Speaker(tts_backend)

    async def start(self) -> None:
        await self.speaker.start()
        for t in REALTIME_EVENT_TYPES:
            self.bus.subscribe(t, self._on_event)

    async def stop(self) -> None:
        await self.speaker.stop()

    def toggle_mute(self) -> None:
        self.engine.set_muted(not self.engine._muted)
        log.info("Mute: %s", self.engine._muted)

    async def _on_event(self, ev: Event) -> None:
        self.tracker.apply_event(ev)
        ctx = self.tracker.snapshot()
        for ann in self.engine.evaluate(ctx):
            await self.speaker.say(ann)
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_realtime_runner.py -v
```
Expected: PASS。

- [ ] **Step 5：把 CLI run 命令接上**

修改 `src/dotacoach/cli.py` 的 `run` 命令：

```python
@main.command()
@click.option("--config", default="config/settings.yaml", type=click.Path())
def run(config: str):
    """Start the realtime layer."""
    import asyncio
    from pathlib import Path
    from dotacoach.config import load_settings
    from dotacoach.events import EventBus
    from dotacoach.gsi.server import serve
    from dotacoach.consolelog.tailer import LogTailer
    from dotacoach.realtime.runner import RealtimeRunner
    from dotacoach.realtime.voice_backends import make_backend
    from dotacoach.realtime.hotkey import HotkeyListener
    from dotacoach.paths import find_dota_root, find_console_log
    import threading

    settings = load_settings(Path(config))
    bus = EventBus()
    backend = make_backend(settings.voice_engine, voice=settings.voice_name)
    runner = RealtimeRunner(bus, Path("config/rules.yaml"), backend)

    async def boot():
        await runner.start()
        # console log tailer
        dota_root = (Path(settings.dota_path) if settings.dota_path
                     else find_dota_root())
        if dota_root:
            tailer = LogTailer(find_console_log(dota_root), bus)
            asyncio.create_task(tailer.run())
        # mute hotkey
        hk = HotkeyListener(settings.mute_hotkey, runner.toggle_mute)
        hk.start()
        # GSI server in background thread
        thread = threading.Thread(
            target=serve, args=(bus, settings.gsi_port), daemon=True)
        thread.start()
        # 阻塞
        while True:
            await asyncio.sleep(3600)

    asyncio.run(boot())
```

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/realtime/runner.py src/dotacoach/cli.py tests/test_realtime_runner.py
git commit -m "feat(realtime): wire GSI + console log + engine + voice in CLI run"
```

---

**Phase 5 检查点：** `dotacoach run` 能起来；开 Dota 试玩，没买 TP 时听到"买 TP"播报。

---

## Phase 6：复盘 - OpenDota 数据采集

### Task 6.1：OpenDota API client

**Files:**
- Create: `src/dotacoach/collector/__init__.py`
- Create: `src/dotacoach/collector/opendota.py`
- Create: `tests/test_opendota.py`

- [ ] **Step 1：写 fail 测试（用 respx mock HTTP）**

`tests/test_opendota.py`：
```python
import httpx
import respx
from dotacoach.collector.opendota import OpenDotaClient

@respx.mock
async def test_get_recent_matches():
    respx.get("https://api.opendota.com/api/players/12345/recentMatches").mock(
        return_value=httpx.Response(200, json=[
            {"match_id": 1, "hero_id": 14, "start_time": 1715800000,
             "duration": 2000, "player_slot": 1, "radiant_win": True,
             "kills": 5, "deaths": 2, "assists": 8,
             "lobby_type": 7, "game_mode": 22}
        ])
    )
    client = OpenDotaClient()
    matches = await client.recent_matches(12345)
    assert len(matches) == 1
    assert matches[0]["match_id"] == 1

@respx.mock
async def test_get_match_detail():
    respx.get("https://api.opendota.com/api/matches/1").mock(
        return_value=httpx.Response(200, json={
            "match_id": 1, "duration": 2000, "start_time": 1715800000,
            "players": []
        })
    )
    client = OpenDotaClient()
    m = await client.match(1)
    assert m["match_id"] == 1
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_opendota.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 client**

`src/dotacoach/collector/__init__.py` 留空。

`src/dotacoach/collector/opendota.py`：
```python
import asyncio
import logging
import httpx

log = logging.getLogger(__name__)
BASE = "https://api.opendota.com/api"

class OpenDotaClient:
    def __init__(self, timeout: float = 15.0, max_retries: int = 3):
        self._client = httpx.AsyncClient(timeout=timeout)
        self.max_retries = max_retries

    async def _get(self, path: str) -> dict | list:
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                r = await self._client.get(f"{BASE}{path}")
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exc = e
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"OpenDota GET {path} failed after retries: {last_exc}")

    async def recent_matches(self, account_id: int) -> list[dict]:
        return await self._get(f"/players/{account_id}/recentMatches")

    async def match(self, match_id: int) -> dict:
        return await self._get(f"/matches/{match_id}")

    async def parse_request(self, match_id: int) -> dict:
        # 触发 OpenDota 解析回放（可选）
        r = await self._client.post(f"{BASE}/request/{match_id}")
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._client.aclose()
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_opendota.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/collector/ tests/test_opendota.py
git commit -m "feat(collector): OpenDota API client with retry"
```

---

### Task 6.2：采集 job（拉取并入库）

**Files:**
- Create: `src/dotacoach/collector/job.py`
- Create: `tests/test_collector_job.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_collector_job.py`：
```python
import httpx
import respx
from dotacoach.collector.job import CollectJob
from dotacoach.collector.opendota import OpenDotaClient
from dotacoach.db.dao import Database

@respx.mock
async def test_collect_persists_matches(tmp_path):
    respx.get("https://api.opendota.com/api/players/12345/recentMatches").mock(
        return_value=httpx.Response(200, json=[
            {"match_id": 1, "hero_id": 14, "start_time": 1715800000,
             "duration": 2000, "player_slot": 1, "radiant_win": True,
             "lobby_type": 7, "game_mode": 22, "kills": 5, "deaths": 2, "assists": 8}
        ])
    )
    respx.get("https://api.opendota.com/api/matches/1").mock(
        return_value=httpx.Response(200, json={
            "match_id": 1, "duration": 2000, "start_time": 1715800000,
            "radiant_win": True, "lobby_type": 7, "game_mode": 22,
            "players": [{
                "account_id": 12345, "hero_id": 14, "isRadiant": True,
                "kills": 5, "deaths": 2, "assists": 8,
                "gold_t": [0,100,200,300], "xp_t": [0,150,300,450],
                "lh_t": [0,5,10,15], "dn_t": [0,1,2,3]
            }]
        })
    )
    db = Database(tmp_path / "test.db")
    db.init_schema()
    client = OpenDotaClient()
    job = CollectJob(client, db)
    n = await job.collect_for_account(12345, since_ts=0)
    assert n == 1
    rows = db.get_matches_since(0)
    assert len(rows) == 1
    assert rows[0]["hero_id"] == 14
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_collector_job.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 job**

`src/dotacoach/collector/job.py`：
```python
import json
import logging
import time
from .opendota import OpenDotaClient
from dotacoach.db.dao import Database

log = logging.getLogger(__name__)

class CollectJob:
    def __init__(self, client: OpenDotaClient, db: Database):
        self.client = client
        self.db = db

    async def collect_for_account(self, account_id: int, since_ts: int) -> int:
        recent = await self.client.recent_matches(account_id)
        new_count = 0
        for m in recent:
            if m["start_time"] < since_ts:
                continue
            detail = await self.client.match(m["match_id"])
            me = next((p for p in detail.get("players", [])
                       if p.get("account_id") == account_id), None)
            if me is None:
                continue
            is_radiant = bool(me.get("isRadiant"))
            win = is_radiant == bool(detail.get("radiant_win"))
            self.db.insert_match(
                match_id=m["match_id"],
                start_time=m["start_time"],
                duration=detail.get("duration", 0),
                hero_id=me["hero_id"],
                is_radiant=is_radiant,
                win=win,
                game_mode=detail.get("game_mode", 0),
                lobby_type=detail.get("lobby_type", 0),
                avg_mmr=detail.get("average_rank"),
                raw_json=json.dumps(detail),
                fetched_at=int(time.time()),
            )
            new_count += 1
        return new_count
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_collector_job.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/collector/job.py tests/test_collector_job.py
git commit -m "feat(collector): job pulls recent matches and persists to SQLite"
```

---

**Phase 6 检查点：** OpenDota client 能拉数据落库。

---

## Phase 7：复盘 - 差异引擎

### Task 7.1：从 SQLite 把局拆成 win/loss 两堆

**Files:**
- Create: `src/dotacoach/analysis/__init__.py`
- Create: `src/dotacoach/analysis/loader.py`
- Create: `tests/test_analysis_loader.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_analysis_loader.py`：
```python
import json
from dotacoach.analysis.loader import load_split
from dotacoach.db.dao import Database

def test_split_by_win(tmp_path):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    for i, win in enumerate([True, False, True]):
        db.insert_match(
            match_id=i, start_time=1000+i, duration=2000, hero_id=14,
            is_radiant=True, win=win, game_mode=22, lobby_type=7,
            avg_mmr=4500,
            raw_json=json.dumps({
                "players":[{"account_id":1,"isRadiant":True,
                            "gold_t":[0,100,200],"xp_t":[0,150,300],
                            "lh_t":[0,5,10],"dn_t":[0,1,2],
                            "kills":5,"deaths":2,"assists":3,
                            "purchase_log":[]}],
                "duration":2000,
            }),
            fetched_at=1000,
        )
    wins, losses = load_split(db, account_id=1, since_ts=0)
    assert len(wins) == 2 and len(losses) == 1
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_analysis_loader.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 loader**

`src/dotacoach/analysis/__init__.py` 留空。

`src/dotacoach/analysis/loader.py`：
```python
import json
from dataclasses import dataclass
from typing import Optional
from dotacoach.db.dao import Database

@dataclass
class MatchRecord:
    match_id: int
    hero_id: int
    win: bool
    duration: int
    player: dict   # 该账号在这局里的 player 数据（OpenDota player obj）

def load_split(db: Database, account_id: int, since_ts: int
               ) -> tuple[list[MatchRecord], list[MatchRecord]]:
    rows = db.get_matches_since(since_ts)
    wins: list[MatchRecord] = []
    losses: list[MatchRecord] = []
    for r in rows:
        raw = json.loads(r["raw_json"])
        me = next((p for p in raw.get("players", [])
                   if p.get("account_id") == account_id), None)
        if me is None:
            continue
        rec = MatchRecord(
            match_id=r["match_id"], hero_id=r["hero_id"], win=bool(r["win"]),
            duration=r["duration"], player=me,
        )
        (wins if rec.win else losses).append(rec)
    return wins, losses
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_analysis_loader.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/__init__.py src/dotacoach/analysis/loader.py tests/test_analysis_loader.py
git commit -m "feat(analysis): split matches into win/loss buckets"
```

---

### Task 7.2：差异指标计算

**Files:**
- Create: `src/dotacoach/analysis/differ.py`
- Create: `tests/test_differ.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_differ.py`：
```python
from dotacoach.analysis.differ import compute_differences
from dotacoach.analysis.loader import MatchRecord

def make(win, gold_t, kills=5, deaths=2):
    return MatchRecord(
        match_id=1, hero_id=14, win=win, duration=2000,
        player={
            "gold_t": gold_t, "xp_t": gold_t, "lh_t": [0]*len(gold_t),
            "dn_t": [0]*len(gold_t), "kills": kills, "deaths": deaths,
            "assists": 0, "purchase_log": [], "gold_per_min": 500,
            "xp_per_min": 600,
        }
    )

def test_gpm_at_10_difference():
    wins = [make(True, [0]+[100*i for i in range(1,30)]) for _ in range(3)]
    losses = [make(False, [0]+[80*i for i in range(1,30)]) for _ in range(3)]
    diffs = compute_differences(wins, losses)
    item = next(d for d in diffs if d.metric == "gold_at_10min")
    assert item.win_mean > item.loss_mean
    assert item.direction == "win_higher"

def test_returns_only_significant_or_large_gaps():
    wins = [make(True, [0]+[100*i for i in range(1,30)]) for _ in range(3)]
    losses = [make(False, [0]+[100*i for i in range(1,30)]) for _ in range(3)]
    diffs = compute_differences(wins, losses)
    # 完全相同的曲线 → 至少 GPM 系列不应被标记
    gpm_items = [d for d in diffs if d.metric.startswith("gold_at_")]
    assert all(not d.significant for d in gpm_items)
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_differ.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 differ**

`src/dotacoach/analysis/differ.py`：
```python
from dataclasses import dataclass
from statistics import mean
from typing import Iterable
from scipy import stats
from .loader import MatchRecord

@dataclass
class Difference:
    metric: str
    win_mean: float
    loss_mean: float
    p_value: float
    direction: str  # "win_higher" | "loss_higher"
    significant: bool

def _safe_get(timeseries: list[int] | None, idx: int) -> float | None:
    if not timeseries or idx >= len(timeseries):
        return None
    return float(timeseries[idx])

def _series_at(records: Iterable[MatchRecord], field: str, minute: int
               ) -> list[float]:
    out = []
    for r in records:
        v = _safe_get(r.player.get(field), minute)
        if v is not None:
            out.append(v)
    return out

def _stat_diff(metric: str, w_vals: list[float], l_vals: list[float],
               p_threshold: float = 0.1) -> Difference | None:
    if len(w_vals) < 2 or len(l_vals) < 2:
        return None
    w_mean, l_mean = mean(w_vals), mean(l_vals)
    if w_mean == l_mean:
        p = 1.0
    else:
        try:
            p = float(stats.ttest_ind(w_vals, l_vals, equal_var=False).pvalue)
        except Exception:
            p = 1.0
    return Difference(
        metric=metric, win_mean=w_mean, loss_mean=l_mean, p_value=p,
        direction="win_higher" if w_mean > l_mean else "loss_higher",
        significant=p < p_threshold,
    )

def compute_differences(wins: list[MatchRecord], losses: list[MatchRecord]
                        ) -> list[Difference]:
    out: list[Difference] = []
    for minute in (5, 10, 15, 20):
        for field, label in [("gold_t", "gold_at"), ("xp_t", "xp_at"),
                             ("lh_t", "lh_at")]:
            d = _stat_diff(
                f"{label}_{minute}min",
                _series_at(wins, field, minute),
                _series_at(losses, field, minute),
            )
            if d:
                out.append(d)

    for fld in ["kills", "deaths", "assists", "gold_per_min", "xp_per_min"]:
        d = _stat_diff(
            fld,
            [r.player.get(fld, 0) for r in wins],
            [r.player.get(fld, 0) for r in losses],
        )
        if d:
            out.append(d)
    return out
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_differ.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/differ.py tests/test_differ.py
git commit -m "feat(analysis): compute statistical differences between win/loss buckets"
```

---

### Task 7.3：英雄池胜率

**Files:**
- Modify: `src/dotacoach/analysis/differ.py`
- Create: `tests/test_hero_pool.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_hero_pool.py`：
```python
from dotacoach.analysis.differ import hero_pool_stats
from dotacoach.analysis.loader import MatchRecord

def make(hero, win):
    return MatchRecord(match_id=1, hero_id=hero, win=win, duration=2000,
                       player={})

def test_hero_pool_winrate():
    matches = [make(14, True), make(14, False), make(14, False),
               make(1, True), make(1, True)]
    stats = hero_pool_stats(matches)
    pudge = next(s for s in stats if s["hero_id"] == 14)
    assert pudge["games"] == 3
    assert pudge["wins"] == 1
    aa = next(s for s in stats if s["hero_id"] == 1)
    assert aa["winrate"] == 1.0
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_hero_pool.py -v
```
Expected: ImportError。

- [ ] **Step 3：扩展 differ**

在 `src/dotacoach/analysis/differ.py` 末尾追加：

```python
def hero_pool_stats(matches: list[MatchRecord]) -> list[dict]:
    by_hero: dict[int, dict] = {}
    for r in matches:
        agg = by_hero.setdefault(r.hero_id, {"hero_id": r.hero_id, "games": 0, "wins": 0})
        agg["games"] += 1
        if r.win:
            agg["wins"] += 1
    out = []
    for agg in by_hero.values():
        agg["winrate"] = agg["wins"] / agg["games"]
        out.append(agg)
    out.sort(key=lambda x: -x["games"])
    return out
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_hero_pool.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/differ.py tests/test_hero_pool.py
git commit -m "feat(analysis): hero pool winrate aggregation"
```

---

**Phase 7 检查点：** 给定一组 win/loss MatchRecord，能算出统计差异和英雄池胜率。

---

## Phase 8：复盘 - Claude API 综合

### Task 8.1：Prompt 模板与响应模型

**Files:**
- Create: `src/dotacoach/analysis/prompts.py`
- Create: `src/dotacoach/analysis/llm_models.py`
- Create: `tests/test_llm_models.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_llm_models.py`：
```python
from dotacoach.analysis.llm_models import LlmReport, Pattern, Task

def test_parse_valid():
    payload = {
        "patterns": [
            {"title": "劣势期决策过激",
             "evidence": "输局 75% 在劣势开团",
             "hypothesis": "把还能打=应该打",
             "verification": "开团前 ping 队友"}
        ],
        "tasks": [
            {"description": "5 局劣势期开团前 ping",
             "metric": "tasks.ping_before_dive",
             "target": 5, "direction": ">=",
             "linked_rule_ids": ["level_disadvantage"]}
        ],
        "hero_pool_advice": "停打 SF，回归 PA"
    }
    r = LlmReport.model_validate(payload)
    assert len(r.patterns) == 1
    assert r.tasks[0].target == 5
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_llm_models.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 models 和 prompts**

`src/dotacoach/analysis/llm_models.py`：
```python
from typing import Literal
from pydantic import BaseModel

class Pattern(BaseModel):
    title: str
    evidence: str
    hypothesis: str
    verification: str

class Task(BaseModel):
    description: str
    metric: str
    target: float
    direction: Literal[">=", "<="]
    linked_rule_ids: list[str] = []

class LlmReport(BaseModel):
    patterns: list[Pattern]
    tasks: list[Task]
    hero_pool_advice: str
```

`src/dotacoach/analysis/prompts.py`：
```python
SYSTEM_PROMPT = """你是一名资深 Dota 2 教练，专门帮高分玩家（曾达超凡）找出比赛中的盲区。
用户每周给你一份"赢局 vs 输局的统计差异"和"英雄池胜率"，你要：

1. 找出 3 条最可能解释胜率差异的核心 pattern。每条 pattern 必须包含：
   - title: 一句话概括
   - evidence: 用具体数据说明
   - hypothesis: 推测原因（用户行为、决策习惯）
   - verification: 用户下一局如何自查

2. 每条 pattern 配 1 条下周训练任务（共 3 条）。每条任务必须可量化、可在比赛中追踪。

3. 给一句英雄池建议（小样本+低胜率英雄停打，推荐回到舒适区）。

只输出 JSON，schema：
{
  "patterns": [{"title": "...", "evidence": "...", "hypothesis": "...", "verification": "..."}],
  "tasks": [{"description": "...", "metric": "...", "target": N, "direction": ">=|<=", "linked_rule_ids": ["..."]}],
  "hero_pool_advice": "..."
}

可用的 metric 名（任务追踪器认识这些）：
- vision.wards_per_game (>= N)
- decisions.tps_per_game (>= N)
- deaths.in_window_18_25min (<= N)
- positioning.deaths_in_enemy_jungle (<= N)
可用的 linked_rule_ids（在比赛中给对应规则加权）：
- no_tp / minimap_neglect / level_disadvantage / roshan_window / enemies_missing
"""

def build_user_prompt(diffs_text: str, hero_pool_text: str,
                      previous_tasks_text: str) -> str:
    return f"""
本周显著差异（赢局 vs 输局）：
{diffs_text}

英雄池：
{hero_pool_text}

上周任务及完成情况：
{previous_tasks_text}

请输出 JSON 报告。
"""
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_llm_models.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/llm_models.py src/dotacoach/analysis/prompts.py tests/test_llm_models.py
git commit -m "feat(analysis): LLM prompt template and response models"
```

---

### Task 8.2：Claude API 调用（含 Prompt Caching）

**Files:**
- Create: `src/dotacoach/analysis/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_llm.py`：
```python
import json
from unittest.mock import MagicMock, AsyncMock
from dotacoach.analysis.llm import generate_report
from dotacoach.analysis.differ import Difference
from dotacoach.analysis.llm_models import LlmReport

async def test_generate_report_calls_claude_with_caching(monkeypatch):
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text=json.dumps({
        "patterns": [{"title":"t","evidence":"e","hypothesis":"h","verification":"v"}],
        "tasks": [{"description":"d","metric":"vision.wards_per_game",
                   "target":5,"direction":">=","linked_rule_ids":[]}],
        "hero_pool_advice": "ok"
    }))]
    fake_client = MagicMock()
    fake_client.messages.create = AsyncMock(return_value=fake_response)
    diffs = [Difference(metric="gold_at_10min", win_mean=600, loss_mean=400,
                        p_value=0.01, direction="win_higher", significant=True)]
    report = await generate_report(
        client=fake_client, model="claude-opus-4-7",
        diffs=diffs, hero_pool=[], previous_tasks=[],
    )
    assert isinstance(report, LlmReport)
    fake_client.messages.create.assert_called_once()
    call = fake_client.messages.create.call_args
    sys_blocks = call.kwargs["system"]
    assert any(b.get("cache_control") == {"type": "ephemeral"} for b in sys_blocks)
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_llm.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 llm**

`src/dotacoach/analysis/llm.py`：
```python
import json
import logging
from anthropic import AsyncAnthropic
from .differ import Difference
from .llm_models import LlmReport
from .prompts import SYSTEM_PROMPT, build_user_prompt

log = logging.getLogger(__name__)

def _diffs_to_text(diffs: list[Difference]) -> str:
    sig = [d for d in diffs if d.significant]
    if not sig:
        return "（无统计显著差异）"
    return "\n".join(
        f"- {d.metric}: 赢均 {d.win_mean:.1f} vs 输均 {d.loss_mean:.1f} "
        f"({d.direction}, p={d.p_value:.3f})"
        for d in sig
    )

def _hero_pool_to_text(rows: list[dict]) -> str:
    if not rows:
        return "（无样本）"
    return "\n".join(
        f"- hero_id={r['hero_id']}: {r['wins']}/{r['games']} "
        f"({r['winrate']*100:.0f}%)"
        for r in rows
    )

def _tasks_to_text(rows: list[dict]) -> str:
    if not rows:
        return "（首周，无历史任务）"
    return "\n".join(
        f"- {r['description']} [target {r['direction']} {r['target']}, "
        f"actual={r.get('actual')}, completed={r.get('completed')}]"
        for r in rows
    )

async def generate_report(
    client: AsyncAnthropic,
    model: str,
    diffs: list[Difference],
    hero_pool: list[dict],
    previous_tasks: list[dict],
) -> LlmReport:
    user_prompt = build_user_prompt(
        _diffs_to_text(diffs),
        _hero_pool_to_text(hero_pool),
        _tasks_to_text(previous_tasks),
    )
    resp = await client.messages.create(
        model=model,
        max_tokens=2000,
        system=[{
            "type": "text", "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = resp.content[0].text
    # Claude 可能会在 JSON 外面带 ```json fence，简单剥一下
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    return LlmReport.model_validate(data)
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_llm.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/llm.py tests/test_llm.py
git commit -m "feat(analysis): Claude API call with prompt caching"
```

---

**Phase 8 检查点：** 给定 mock Claude 客户端，能产出结构化的 LlmReport。

---

## Phase 9：复盘 - 报告渲染

### Task 9.1：Markdown 报告渲染

**Files:**
- Create: `src/dotacoach/analysis/report.py`
- Create: `tests/test_report.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_report.py`：
```python
from dotacoach.analysis.report import render_markdown
from dotacoach.analysis.llm_models import LlmReport, Pattern, Task

def test_render_basic():
    r = LlmReport(
        patterns=[
            Pattern(title="t1", evidence="e1", hypothesis="h1", verification="v1")
        ],
        tasks=[
            Task(description="d1", metric="vision.wards_per_game",
                 target=5, direction=">=", linked_rule_ids=["enemies_missing"])
        ],
        hero_pool_advice="停打 SF",
    )
    md = render_markdown(
        week_label="2026-W20", report=r,
        previous_task_results=[
            {"description":"上周任务","target":3,"direction":">=",
             "actual":4,"completed":True}
        ],
    )
    assert "2026-W20" in md
    assert "## 上周任务回顾" in md
    assert "✅" in md
    assert "## 本周 3 大 pattern" in md or "## 本周核心 pattern" in md
    assert "t1" in md
    assert "停打 SF" in md
    assert "vision.wards_per_game" in md
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_report.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 report**

`src/dotacoach/analysis/report.py`：
```python
from .llm_models import LlmReport

def _check_mark(completed: bool | None) -> str:
    if completed is True:
        return "✅"
    if completed is False:
        return "❌"
    return "⚠️"

def render_markdown(week_label: str, report: LlmReport,
                    previous_task_results: list[dict]) -> str:
    parts = [f"# Dota Coach 周报告 · {week_label}", ""]

    parts.append("## 上周任务回顾")
    if not previous_task_results:
        parts.append("（首周，无历史任务）")
    else:
        for t in previous_task_results:
            mark = _check_mark(t.get("completed"))
            parts.append(
                f"- {mark} {t['description']} "
                f"（目标 {t['direction']} {t['target']}，实际 {t.get('actual')}）"
            )
    parts.append("")

    parts.append("## 本周核心 pattern")
    for i, p in enumerate(report.patterns, 1):
        parts += [
            f"### {i}. {p.title}",
            f"- **现象**：{p.evidence}",
            f"- **假设**：{p.hypothesis}",
            f"- **自查**：{p.verification}",
            "",
        ]

    parts.append("## 英雄池建议")
    parts.append(report.hero_pool_advice)
    parts.append("")

    parts.append("## 下周训练任务")
    for i, t in enumerate(report.tasks, 1):
        rules = ", ".join(t.linked_rule_ids) or "—"
        parts.append(
            f"{i}. {t.description}（指标 `{t.metric}` {t.direction} {t.target}；"
            f"关联规则：{rules}）"
        )

    return "\n".join(parts) + "\n"
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_report.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/report.py tests/test_report.py
git commit -m "feat(analysis): markdown report rendering"
```

---

**Phase 9 检查点：** 能从 LlmReport 对象渲染出完整 markdown。

---

## Phase 10：飞书推送

### Task 10.1：Feishu webhook

**Files:**
- Create: `src/dotacoach/notify/__init__.py`
- Create: `src/dotacoach/notify/feishu.py`
- Create: `tests/test_feishu.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_feishu.py`：
```python
import httpx
import respx
from dotacoach.notify.feishu import send_feishu_text

@respx.mock
async def test_post_text():
    route = respx.post("https://example.com/hook").mock(
        return_value=httpx.Response(200, json={"code": 0})
    )
    ok = await send_feishu_text("https://example.com/hook", "title", "body")
    assert ok is True
    assert route.called
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_feishu.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现**

`src/dotacoach/notify/__init__.py` 留空。

`src/dotacoach/notify/feishu.py`：
```python
import logging
import httpx

log = logging.getLogger(__name__)

async def send_feishu_text(webhook_url: str, title: str, content: str) -> bool:
    body = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": content}]],
                }
            }
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(webhook_url, json=body)
            r.raise_for_status()
            return True
        except Exception as e:
            log.warning("feishu push failed: %s", e)
            return False
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_feishu.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/notify/ tests/test_feishu.py
git commit -m "feat(notify): feishu webhook push"
```

---

## Phase 11：任务追踪器

### Task 11.1：任务持久化与加载

**Files:**
- Create: `src/dotacoach/tasks/__init__.py`
- Create: `src/dotacoach/tasks/tracker.py`
- Create: `tests/test_tasks_tracker.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_tasks_tracker.py`：
```python
import time
from dotacoach.tasks.tracker import TaskTracker
from dotacoach.db.dao import Database
from dotacoach.analysis.llm_models import Task

def test_save_and_load_current_tasks(tmp_path):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    tracker = TaskTracker(db)
    tracker.set_current_tasks("2026-W20", [
        Task(description="d", metric="vision.wards_per_game",
             target=5, direction=">=", linked_rule_ids=["enemies_missing"])
    ])
    current = tracker.get_current_tasks()
    assert len(current) == 1
    assert current[0]["metric"] == "vision.wards_per_game"

def test_finalize_marks_completed(tmp_path):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    tracker = TaskTracker(db)
    tracker.set_current_tasks("2026-W20", [
        Task(description="d", metric="m", target=5, direction=">=")
    ])
    results = tracker.finalize_week("2026-W20", actuals={"m": 6.0})
    assert results[0]["completed"] is True
    assert results[0]["actual"] == 6.0
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_tasks_tracker.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 tracker**

`src/dotacoach/tasks/__init__.py` 留空。

`src/dotacoach/tasks/tracker.py`：
```python
import json
import time
from dotacoach.db.dao import Database
from dotacoach.analysis.llm_models import Task

class TaskTracker:
    def __init__(self, db: Database):
        self.db = db

    def set_current_tasks(self, week_label: str, tasks: list[Task]) -> None:
        for t in tasks:
            self.db.conn.execute(
                """INSERT INTO tasks
                (week_label, description, metric, target, direction,
                 linked_rule_ids, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (week_label, t.description, t.metric, t.target, t.direction,
                 json.dumps(t.linked_rule_ids), int(time.time())),
            )
        self.db.conn.commit()

    def get_current_tasks(self) -> list[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM tasks WHERE completed IS NULL ORDER BY id DESC"
        )
        return [dict(r) for r in cur.fetchall()]

    def finalize_week(self, week_label: str, actuals: dict[str, float]) -> list[dict]:
        cur = self.db.conn.execute(
            "SELECT * FROM tasks WHERE week_label = ?", (week_label,)
        )
        results = []
        for row in cur.fetchall():
            metric = row["metric"]
            actual = actuals.get(metric)
            if actual is None:
                completed = None
            elif row["direction"] == ">=":
                completed = actual >= row["target"]
            else:
                completed = actual <= row["target"]
            self.db.conn.execute(
                "UPDATE tasks SET completed = ?, actual = ? WHERE id = ?",
                (1 if completed else 0 if completed is False else None,
                 actual, row["id"]),
            )
            results.append({**dict(row), "completed": completed, "actual": actual})
        self.db.conn.commit()
        return results
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_tasks_tracker.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/tasks/ tests/test_tasks_tracker.py
git commit -m "feat(tasks): task tracker persists and finalizes weekly"
```

---

### Task 11.2：实时层规则优先级加权

**Files:**
- Create: `src/dotacoach/tasks/linker.py`
- Create: `tests/test_tasks_linker.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_tasks_linker.py`：
```python
from dotacoach.tasks.linker import boost_rules_for_tasks
from dotacoach.realtime.rule import Rule

def test_boost_lowers_cooldown_for_linked_rules():
    rules = [
        Rule(id="enemies_missing", category="m", priority="tactical",
             cooldown_s=20, when="True", say="x"),
        Rule(id="other", category="o", priority="tactical",
             cooldown_s=30, when="True", say="y"),
    ]
    tasks = [{"linked_rule_ids": '["enemies_missing"]', "description":"d",
              "metric":"m","target":5,"direction":">="}]
    out = boost_rules_for_tasks(rules, tasks)
    by_id = {r.id: r for r in out}
    # linked rule 优先级提升 + 冷却减半
    assert by_id["enemies_missing"].priority == "critical"
    assert by_id["enemies_missing"].cooldown_s == 10
    assert by_id["other"].priority == "tactical"
    assert by_id["other"].cooldown_s == 30
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_tasks_linker.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 linker**

`src/dotacoach/tasks/linker.py`：
```python
import json
from dotacoach.realtime.rule import Rule

def boost_rules_for_tasks(rules: list[Rule], tasks: list[dict]) -> list[Rule]:
    linked: set[str] = set()
    for t in tasks:
        ids = t.get("linked_rule_ids")
        if isinstance(ids, str):
            try:
                ids = json.loads(ids)
            except Exception:
                ids = []
        for rid in (ids or []):
            linked.add(rid)
    out = []
    for r in rules:
        if r.id in linked:
            out.append(r.model_copy(update={
                "priority": "critical",
                "cooldown_s": max(5, r.cooldown_s // 2),
            }))
        else:
            out.append(r)
    return out
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_tasks_linker.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/tasks/linker.py tests/test_tasks_linker.py
git commit -m "feat(tasks): boost realtime rules linked to current tasks"
```

---

### Task 11.3：把 boost 接入 RealtimeRunner

**Files:**
- Modify: `src/dotacoach/realtime/runner.py`
- Create: `tests/test_runner_with_tasks.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_runner_with_tasks.py`：
```python
import asyncio
from pathlib import Path
from dotacoach.events import EventBus
from dotacoach.realtime.runner import RealtimeRunner
from dotacoach.realtime.voice import FakeBackend

async def test_runner_accepts_task_list(tmp_path):
    rules_yaml = tmp_path / "rules.yaml"
    rules_yaml.write_text("""
rules:
  - id: r_a
    category: c
    priority: tactical
    cooldown_s: 30
    when: "True"
    say: "x"
""")
    bus = EventBus()
    runner = RealtimeRunner(
        bus, rules_yaml, FakeBackend(),
        current_tasks=[{"linked_rule_ids":'["r_a"]',"description":"d",
                        "metric":"m","target":1,"direction":">="}],
    )
    assert runner.engine.rules[0].priority == "critical"
    assert runner.engine.rules[0].cooldown_s == 15
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_runner_with_tasks.py -v
```
Expected: AssertionError 或 TypeError。

- [ ] **Step 3：扩展 runner**

修改 `src/dotacoach/realtime/runner.py` 的 `__init__`：

```python
from dotacoach.tasks.linker import boost_rules_for_tasks

class RealtimeRunner:
    def __init__(self, bus: EventBus, rules_path: Path, tts_backend: TtsBackend,
                 current_tasks: list[dict] | None = None):
        self.bus = bus
        self.tracker = GameStateTracker()
        rules = load_rules(rules_path)
        if current_tasks:
            rules = boost_rules_for_tasks(rules, current_tasks)
        self.engine = RuleEngine(rules)
        self.speaker = Speaker(tts_backend)
```

- [ ] **Step 4：跑全部 runner 测试**

```bash
uv run pytest tests/test_realtime_runner.py tests/test_runner_with_tasks.py -v
```
Expected: PASS。

- [ ] **Step 5：把 CLI run 命令也接上当前任务**

修改 `src/dotacoach/cli.py` 的 `run` 命令：在创建 Database + TaskTracker 后，把 `current_tasks` 传给 `RealtimeRunner`：

```python
from dotacoach.tasks.tracker import TaskTracker
from dotacoach.db.dao import Database
...
db = Database(Path("data/coach.db"))
db.init_schema()
tracker = TaskTracker(db)
runner = RealtimeRunner(
    bus, Path("config/rules.yaml"), backend,
    current_tasks=tracker.get_current_tasks(),
)
```

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/realtime/runner.py src/dotacoach/cli.py tests/test_runner_with_tasks.py
git commit -m "feat(tasks): wire current tasks into realtime rule boosting"
```

---

**Phase 11 检查点：** 当前任务关联的规则优先级被自动提升。

---

## Phase 12：周复盘端到端 + 调度

### Task 12.1：周复盘 pipeline 串联

**Files:**
- Create: `src/dotacoach/analysis/pipeline.py`
- Create: `tests/test_analysis_pipeline.py`

- [ ] **Step 1：写 fail 测试（mock Claude）**

`tests/test_analysis_pipeline.py`：
```python
import json
import time
from unittest.mock import MagicMock, AsyncMock
from dotacoach.analysis.pipeline import run_weekly_pipeline
from dotacoach.db.dao import Database

async def test_pipeline_produces_report(tmp_path, monkeypatch):
    db = Database(tmp_path / "t.db")
    db.init_schema()
    # 塞两局：1 win + 1 loss
    for i, win in enumerate([True, False]):
        db.insert_match(
            match_id=i, start_time=int(time.time())-100*(i+1), duration=2000,
            hero_id=14, is_radiant=True, win=win, game_mode=22, lobby_type=7,
            avg_mmr=4500,
            raw_json=json.dumps({
                "duration":2000,"radiant_win":win,
                "players":[{"account_id":42,"isRadiant":True,
                            "hero_id":14,"kills":5,"deaths":2,"assists":3,
                            "gold_t":[100*j for j in range(30)],
                            "xp_t":[150*j for j in range(30)],
                            "lh_t":[5*j for j in range(30)],
                            "dn_t":[j for j in range(30)],
                            "purchase_log":[],
                            "gold_per_min":500,"xp_per_min":600}],
            }),
            fetched_at=int(time.time()),
        )
    fake_resp = MagicMock()
    fake_resp.content = [MagicMock(text=json.dumps({
        "patterns":[{"title":"t","evidence":"e","hypothesis":"h","verification":"v"}],
        "tasks":[{"description":"d","metric":"vision.wards_per_game",
                  "target":5,"direction":">=","linked_rule_ids":[]}],
        "hero_pool_advice":"ok"
    }))]
    fake_client = MagicMock()
    fake_client.messages.create = AsyncMock(return_value=fake_resp)

    md, report = await run_weekly_pipeline(
        db=db, account_id=42, week_label="2026-W20",
        anthropic_client=fake_client, model="claude-opus-4-7",
        since_ts=0,
    )
    assert "2026-W20" in md
    assert "t" in md
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_analysis_pipeline.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 pipeline**

`src/dotacoach/analysis/pipeline.py`：
```python
import time
from anthropic import AsyncAnthropic
from dotacoach.db.dao import Database
from dotacoach.tasks.tracker import TaskTracker
from .loader import load_split
from .differ import compute_differences, hero_pool_stats
from .llm import generate_report
from .report import render_markdown

async def run_weekly_pipeline(
    db: Database,
    account_id: int,
    week_label: str,
    anthropic_client: AsyncAnthropic,
    model: str,
    since_ts: int,
) -> tuple[str, "LlmReport"]:
    wins, losses = load_split(db, account_id, since_ts)
    diffs = compute_differences(wins, losses)
    pool = hero_pool_stats(wins + losses)

    # 上周任务自动 finalize（actuals 用空字典 → completed=None；后续 11.4 可加真正测算）
    tracker = TaskTracker(db)
    previous = tracker.finalize_week(_previous_week_label(week_label), actuals={})

    report = await generate_report(
        client=anthropic_client, model=model,
        diffs=diffs, hero_pool=pool, previous_tasks=previous,
    )
    tracker.set_current_tasks(week_label, report.tasks)

    md = render_markdown(week_label, report, previous)
    db.conn.execute(
        "INSERT OR REPLACE INTO reports (week_label, generated_at, markdown) VALUES (?,?,?)",
        (week_label, int(time.time()), md),
    )
    db.conn.commit()
    return md, report

def _previous_week_label(week_label: str) -> str:
    # 简化：取本年的 W{n-1}；跨年场景留 TODO（首周无前周也安全）
    year, w = week_label.split("-W")
    n = int(w) - 1
    if n < 1:
        return f"{int(year)-1}-W52"
    return f"{year}-W{n:02d}"
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_analysis_pipeline.py -v
```
Expected: PASS。

- [ ] **Step 5：commit**

```bash
git add src/dotacoach/analysis/pipeline.py tests/test_analysis_pipeline.py
git commit -m "feat(analysis): end-to-end weekly pipeline"
```

---

### Task 12.2：CLI weekly 命令接通

**Files:**
- Modify: `src/dotacoach/cli.py`

- [ ] **Step 1：替换 weekly 命令**

修改 `src/dotacoach/cli.py` 的 `weekly` 命令：

```python
@main.command()
@click.option("--config", default="config/settings.yaml", type=click.Path())
@click.option("--since-days", default=7, type=int)
def weekly(config: str, since_days: int):
    """Run the weekly review pipeline now."""
    import asyncio
    import time
    from datetime import datetime
    from pathlib import Path
    from anthropic import AsyncAnthropic
    from dotacoach.config import load_settings
    from dotacoach.db.dao import Database
    from dotacoach.collector.opendota import OpenDotaClient
    from dotacoach.collector.job import CollectJob
    from dotacoach.analysis.pipeline import run_weekly_pipeline
    from dotacoach.notify.feishu import send_feishu_text

    settings = load_settings(Path(config))

    async def go():
        db = Database(Path("data/coach.db"))
        db.init_schema()
        client = OpenDotaClient()
        await CollectJob(client, db).collect_for_account(
            settings.steam_id_32,
            since_ts=int(time.time()) - since_days * 86400,
        )
        await client.close()
        anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        week_label = datetime.now().strftime("%Y-W%V")
        md, _ = await run_weekly_pipeline(
            db=db, account_id=settings.steam_id_32, week_label=week_label,
            anthropic_client=anthropic, model="claude-opus-4-7",
            since_ts=int(time.time()) - since_days * 86400,
        )
        out = Path("data/reports") / f"{week_label}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        click.echo(f"Report written: {out}")
        if settings.feishu_webhook_url:
            await send_feishu_text(
                settings.feishu_webhook_url,
                f"Dota Coach 周报告 {week_label}",
                md[:1500] + ("…" if len(md) > 1500 else ""),
            )

    asyncio.run(go())
```

- [ ] **Step 2：手动验证（占位）**

```bash
uv run dotacoach weekly --help
```
Expected: 看到 since-days 选项。

- [ ] **Step 3：commit**

```bash
git add src/dotacoach/cli.py
git commit -m "feat(cli): weekly command runs full review pipeline"
```

---

### Task 12.3：APScheduler 周自动调度

**Files:**
- Create: `src/dotacoach/scheduler.py`
- Modify: `src/dotacoach/cli.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_scheduler.py`：
```python
from dotacoach.scheduler import build_scheduler

def test_build_scheduler_registers_weekly():
    fired = []
    def cb():
        fired.append(1)
    sched = build_scheduler(cb)
    jobs = sched.get_jobs()
    assert any(j.id == "weekly_review" for j in jobs)
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_scheduler.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 scheduler**

`src/dotacoach/scheduler.py`：
```python
from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

def build_scheduler(weekly_callback: Callable) -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    sched.add_job(
        weekly_callback,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="weekly_review",
    )
    return sched
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_scheduler.py -v
```
Expected: PASS。

- [ ] **Step 5：把 scheduler 接进 run 命令**

在 `src/dotacoach/cli.py` 的 `run` 命令的 `boot()` 函数里：

```python
from dotacoach.scheduler import build_scheduler

async def weekly_in_bg():
    # 复用 weekly 命令的 go() 逻辑：抽取为模块级 _run_weekly(settings)
    from dotacoach.cli import _run_weekly  # 见下一步
    await _run_weekly(settings)

sched = build_scheduler(weekly_in_bg)
sched.start()
```

并在 `cli.py` 顶部抽出 `async def _run_weekly(settings): ...`，把 weekly 命令里的 `go()` 函数体放进去，weekly 命令本身改为：
```python
asyncio.run(_run_weekly(settings))
```

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/scheduler.py src/dotacoach/cli.py tests/test_scheduler.py
git commit -m "feat(scheduler): weekly review auto-trigger via APScheduler"
```

---

**Phase 12 检查点：** `dotacoach weekly` 完整跑通；`dotacoach run` 常驻进程内含周日调度。

---

## Phase 13：GSI 安装脚本

### Task 13.1：install-gsi 命令

**Files:**
- Create: `src/dotacoach/install_gsi.py`
- Modify: `src/dotacoach/cli.py`
- Create: `tests/test_install_gsi.py`

- [ ] **Step 1：写 fail 测试**

`tests/test_install_gsi.py`：
```python
from pathlib import Path
from dotacoach.install_gsi import write_gsi_cfg

def test_writes_cfg_to_correct_dir(tmp_path):
    dota_root = tmp_path / "dota 2 beta"
    cfg_dir = dota_root / "game" / "dota" / "cfg" / "gamestate_integration"
    cfg_dir.mkdir(parents=True)
    out = write_gsi_cfg(dota_root, port=4000)
    assert out.exists()
    assert "URI" in out.read_text()
    assert "4000" in out.read_text()
```

- [ ] **Step 2：跑测试看 fail**

```bash
uv run pytest tests/test_install_gsi.py -v
```
Expected: ImportError。

- [ ] **Step 3：实现 install**

`src/dotacoach/install_gsi.py`：
```python
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
```

- [ ] **Step 4：跑测试**

```bash
uv run pytest tests/test_install_gsi.py -v
```
Expected: PASS。

- [ ] **Step 5：把 install-gsi CLI 接通**

修改 `src/dotacoach/cli.py` 的 `install_gsi` 命令：

```python
@main.command("install-gsi")
@click.option("--config", default="config/settings.yaml", type=click.Path())
def install_gsi(config: str):
    """Install Valve GSI config to the Dota 2 directory."""
    from pathlib import Path
    from dotacoach.config import load_settings
    from dotacoach.paths import find_dota_root
    from dotacoach.install_gsi import write_gsi_cfg

    settings = load_settings(Path(config))
    dota_root = (Path(settings.dota_path) if settings.dota_path
                 else find_dota_root())
    if dota_root is None:
        click.echo("ERR: 找不到 Dota 安装目录，请在 settings.yaml 设置 dota_path")
        raise SystemExit(1)
    out = write_gsi_cfg(dota_root, port=settings.gsi_port)
    click.echo(f"GSI cfg written: {out}")
    click.echo("接下来：把启动选项加上 -gamestateintegration -condebug")
```

- [ ] **Step 6：commit**

```bash
git add src/dotacoach/install_gsi.py src/dotacoach/cli.py tests/test_install_gsi.py
git commit -m "feat(install): GSI config writer with CLI command"
```

---

**Phase 13 检查点：** `dotacoach install-gsi` 在本机能正确放置 cfg。

---

## Phase 14：端到端烟雾测试 + 文档

### Task 14.1：跑完整测试套件

- [ ] **Step 1：跑全部 pytest**

```bash
uv run pytest -v
```
Expected: 全 PASS。

- [ ] **Step 2：跑 lint（可选）**

```bash
uv pip install ruff
uv run ruff check src/ tests/
```
修任何报错。

- [ ] **Step 3：commit lint 修复（如有）**

```bash
git add -A && git commit -m "chore: lint cleanup"
```

---

### Task 14.2：补 README

**Files:**
- Modify: `README.md`

- [ ] **Step 1：写完整 README**

```markdown
# Dota Coach

Personal Dota 2 coach. Realtime advice during games + weekly blind-spot
analysis.

See [设计文档](docs/specs/2026-05-15-dota-coach-design.md) for the full design.

## Install

```bash
uv venv
uv pip install -e ".[dev]"
cp config/settings.example.yaml config/settings.yaml
# 编辑 settings.yaml 填入 Steam 32-bit ID + Anthropic API key + Feishu webhook
uv run dotacoach install-gsi
```

In Steam → Dota 2 → 属性 → 启动选项加：
```
-gamestateintegration -condebug
```

## Run

```bash
# 实时层（常驻）
uv run dotacoach run

# 手动触发周报告
uv run dotacoach weekly
```

实时层会每周日凌晨 03:00 自动跑一次复盘。

## Mute

按 F8 切换全局 mute（可在 settings.yaml 改键位）。
```

- [ ] **Step 2：commit**

```bash
git add README.md
git commit -m "docs: complete README"
```

---

### Task 14.3：实景烟雾测试（手动）

- [ ] **Step 1：开 Dota 2，进 demo / bot 局**

启动后 `dotacoach run` 应能：
- 通过 GSI 接到 payload（看日志）
- 没买 TP 时听到"买 TP"
- 按 F8 后无声音；再按一次恢复

- [ ] **Step 2：手动触发一次周报告**

```bash
uv run dotacoach weekly --since-days 30
```

确认：
- `data/reports/<week>.md` 生成
- 飞书收到推送
- markdown 内容包含 3 条 pattern + 任务

- [ ] **Step 3：把上面的烟雾测试结论简单记录到 README 的 "Tested with" 一节**

- [ ] **Step 4：final commit**

```bash
git add -A && git commit -m "chore: smoke test complete, project ready"
```

---

**Phase 14 检查点：** 全部模块端到端跑通，可以日常使用。

---

## 后续可扩展（不在本次范围）

- 本地 replay 解析（用 `clarity-rs`/`manta`，加坐标时序）
- HTML dashboard（替代 markdown）
- 对话式问答接口
- 任务进度自动从赛中实时统计（目前 `finalize_week` 的 actuals 还是空字典，可在 task tracker 中扩展实时累加）
- 每英雄定制规则集
