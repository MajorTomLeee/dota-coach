# Dota Coach 设计文档

- **日期**：2026-05-15
- **状态**：已与用户确认，待实施计划
- **目标用户**：单人使用（作者本人，统帅~传奇段位，曾达超凡）

## 1. 项目动机

用户已是经验丰富的高分玩家，胜率良好但比赛时间有限，瓶颈在于**自我认知盲区**——输了说不清为什么输、赢了不知道是不是真的打得好。

通用 stats 工具（OpenDota、Dotabuff、Dota Plus）对该用户已无边际价值。需要一个**私人教练**式工具：在有限对局中最大化学习效率，把水平推过原有天花板。

## 2. 目标与非目标

### 目标

- **临场决策辅助**：实时层在游戏中提供合规的提醒（计时、决策、节奏），帮助消除低级失误
- **盲区识别**：每周自动从对局数据中挖掘"赢局 vs 输局"的差异模式，输出 3 条核心 pattern
- **训练闭环**：每条 pattern 配 1 条可量化的下周训练任务，下周报告自动验证改善
- **跨平台**：Mac 和 Windows 一份代码

### 非目标

- 不做作弊：不读游戏内存、不获取视野外信息、不自动操作
- 不做泛用工具：仅服务一个用户的提升，不考虑多用户/SaaS
- 不取代 Dota Plus 的基础功能（出装推荐等）

## 3. 合规边界

| 数据源 | 来源 | 合规性 |
|---|---|---|
| GSI（Game State Integration）| Valve 官方推送的 JSON 流 | ✅ 官方支持 |
| Console log | Dota 启动参数 `-condebug` 输出的日志 | ✅ Valve 自己提供 |
| OpenDota API | 第三方公开 API，赛后数据 | ✅ 公开数据 |
| 游戏内存读取 | — | ❌ 封号风险，**绝不使用** |
| 屏幕 OCR 推断敌方信息 | — | ⚠️ MVP 不做，后续如需谨慎评估 |

## 4. 系统总览

### 4.1 闭环

```
打比赛
  ↓ (实时层介入)
GSI + Console log → 规则引擎 → TTS 语音/通知 → 用户决策
  ↓ (赛后)
OpenDota API 拉本局完整数据 → SQLite
  ↓ (每周日凌晨自动触发)
模式挖掘（赢局 vs 输局差异分析）→ Claude API 综合 → 周报告
  ↓
生成下周训练任务（3 条）
  ↓
下周打比赛时实时层加成对应任务的规则优先级
  ↓ (一周后)
下周报告验证：上周任务 ✅/⚠️/❌
```

### 4.2 模块划分

5 个独立模块，各自有清晰的输入/输出边界，可独立单测。

| ID | 模块 | 职责 | 输入 | 输出 |
|---|---|---|---|---|
| ① | GSI 接收器 | 起本地 HTTP server，接 Valve 推送，标准化为事件 | 原始 JSON | 事件流 |
| ② | 实时规则引擎 | 订阅事件流，匹配规则，触发提醒 | 事件流 | 提醒动作（文字+TTS） |
| ③ | 数据采集器 | 触发/定时拉 OpenDota，落库 | Steam ID | SQLite 行 |
| ④ | 模式挖掘器 | 跑统计差异 + 调 Claude API 出报告 | N 局数据 | 报告 markdown + 任务列表 |
| ⑤ | 任务追踪器 | 周内监控本周任务进度 | 任务定义 + 实时事件 | 进度状态 |

**模块解耦原则：**
- 模块间通过 SQLite 表 / 文件 / 内存事件总线通信，不引入 message broker
- 实时层（① ② ⑤）和复盘层（③ ④）完全独立，任一挂掉不影响另一
- 全本地运行，外联仅 OpenDota API 和 Anthropic API

## 5. 实时层详细设计

### 5.1 数据源

- **GSI**（player integration）：仅覆盖**自己 + 队友**——HP/Mana/金钱/物品/技能 CD/位置、游戏时间、Roshan 估计状态、神符刷新计时
- **Console log**（启用 `-condebug`）：所有用户视野内的战斗事件，包括敌方技能释放、击杀链、伤害事件——这是**敌方信息的唯一合规来源**

**关键设计含义：**
- "敌方 N+ 缺人"类规则依赖 console log 中"敌方 X 距上次出现已 30s+"的近似判断，而非真实小地图位置
- 敌方关键技能 CD 估算完全靠 console log 解析（看到释放的瞬间打时间戳，按公开 CD 表倒推）

### 5.2 规则分类

| 类别 | 触发示例 | 语音示例 |
|---|---|---|
| 🗺️ 地图意识 | 60s 未看小地图 / 敌方 2+ 缺人 | "下路缺，注意 gank" |
| ⏱️ 节奏决策 | 神符前 30s + 你近 / 肉山可打窗口 | "30 秒上路神符" |
| 💰 个人经济 | 没 TP / 买活够了没用 / 大件差 X 金 | "买 TP" |
| 🎯 大招追踪 | 看到敌方关键大释放 → CD-15s 前提醒 | "莱恩大快好了" |
| 🧠 形势判断 | 等级劣势 ≥ 2 别冒进 / 经济顺风可打架 | "等级落后，回线刷" |

完整规则集在 `config/rules.yaml` 中以声明式定义，无需改代码即可增删。

### 5.3 核心机制

1. **优先级队列 + 防刷屏**：每条规则有冷却窗口（默认 30s）和优先级（critical/tactical/housekeeping），同一时刻只播最高优
2. **战斗静默**：检测到短时间内多次伤害事件 = 团战中，自动 mute 非紧急提醒
3. **任务联动**：模块 ⑤ 把本周任务对应的指标加权到规则优先级，让用户在当下就能改进
4. **TTS 引擎**：主用 edge-tts（云、跨平台、中文音质好），离线兜底用 pyttsx3（Win 走 SAPI，Mac 走 NSSpeechSynthesizer）
5. **语句风格**：≤8 字，命令式；高优中断低优播报
6. **全局 mute 热键**：用户随时可禁用全部播报

### 5.4 配置示例

```yaml
# config/rules.yaml
rules:
  - id: no_tp
    category: economy
    priority: critical
    cooldown_s: 60
    when: "player.gold >= 50 and 'tpscroll' not in player.items"
    say: "买 TP"

  - id: minimap_neglect
    category: map_awareness
    priority: tactical
    cooldown_s: 30
    when: "now - last_minimap_view_ts > 60"
    say: "看小地图"

  - id: enemy_ult_soon
    category: cooldown_tracking
    priority: tactical
    cooldown_s: 0
    when: "enemy_ult_estimated_cd_remaining < 15"
    say: "{enemy_hero} 大快好了"
```

## 6. 复盘层详细设计

### 6.1 Pipeline

```
拉数据 → 统计差异 → LLM 综合 → 出报告 → 生成任务
```

每周日凌晨 03:00 由 APScheduler 触发。

### 6.2 数据采集

- **来源**：OpenDota API（免费，60 req/min 够用）
- **范围**：最近 7 天所有 ranked 场次（统一定义："本周" = 截至触发时刻往前推 7×24 小时）
- **关键字段**：
  - 局基本信息：英雄、胜负、持续时间、对局时间戳、模式
  - 时间序列：每分钟 GPM/XPM/networth/lh/dn
  - 战斗事件：死亡时间戳+坐标、击杀链、participation
  - 决策指标：TP 数、烟次数、肉山参与
  - 视野：ward 放置数 + 得分
- **存储**：SQLite，schema 极简（matches + match_events 两张表）

### 6.3 差异引擎

把本周对局分为**赢局**和**输局**两个 bucket，对以下维度做对比：

| 维度 | 比较方法 | 显著性判定 |
|---|---|---|
| 经济曲线 | 5/10/15/20 min GPM 均值差 | 简单 t-test，p<0.1 标记 |
| 死亡分布 | 时间直方图 + 坐标热点 | KS-test |
| 决策频次 | TP/烟/肉山参与率均值差 | t-test |
| 英雄池 | 每英雄胜率 + 样本量 | 直接列出胜率 < 40% 且样本 ≥ 3 的 |
| 视野 | wards 数 + 得分均值差 | t-test |

输出"显著差异项"列表（含数值和方向），不直接给结论，留给 LLM 综合。

### 6.4 LLM 综合

调用 Claude API（claude-opus-4-7），启用 **Prompt Caching**。

**输入**：
- System prompt（缓存，固定）：教练人设、报告格式要求
- User prompt（动态）：本周显著差异项列表 + 3-5 个典型局的事件序列摘要 + 上周任务及其完成情况

**输出**：3 条 pattern + 3 条下周任务，每条 pattern 包含：
- 现象（数据证据）
- 假设原因（推理）
- 验证方法（自查方式）

每条任务包含：
- 描述
- 量化指标（下周报告自动 check）
- 关联到的实时规则 id（让模块 ⑤ 在赛中加权）

### 6.5 报告输出

- **格式**：Markdown 文件落到 `data/reports/YYYY-WW.md`
- **推送**：飞书 webhook（用户已配置）→ 手机
- **结构**：
  1. 上周任务回顾（✅/⚠️/❌ + 数据对比）
  2. 本周 3 大 pattern
  3. 英雄池建议
  4. 下周 3 条任务

## 7. 技术栈

| 层 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.11+ | 跨平台、生态丰富 |
| GSI 接收 | FastAPI + uvicorn | 异步、轻量、Valve 推 POST 处理简洁 |
| 数据库 | SQLite | 单文件、零运维、跨平台 |
| HTTP 客户端 | httpx | OpenDota API |
| TTS | edge-tts（主）+ pyttsx3（兜底） | 跨平台、中文音质 |
| 文件监听 | watchdog | console log tail，跨平台 |
| LLM | anthropic SDK + Prompt Caching | 周报告生成 |
| 调度 | APScheduler | 跨平台、比 cron/任务计划程序更可控 |
| 配置 | YAML + pydantic 校验 | 改规则不改代码 |
| 包管理 | uv | 快、跨平台 |
| 测试 | pytest + GSI mock fixtures | 模块独立测试 |

## 8. 项目结构

```
dota-coach/
├── pyproject.toml
├── README.md
├── config/
│   ├── settings.yaml          # Steam 32位 ID、API keys、Dota 路径
│   ├── rules.yaml             # 实时规则定义
│   └── tasks.yaml             # 当前训练任务（每周更新）
├── src/dotacoach/
│   ├── __init__.py
│   ├── cli.py                 # 入口：dotacoach run / weekly / install-gsi
│   ├── gsi/
│   │   ├── server.py          # FastAPI 接收器
│   │   └── parser.py          # JSON → 事件
│   ├── consolelog/
│   │   ├── tailer.py          # watchdog 文件追加
│   │   └── parser.py          # 解析关键事件（敌方技能释放等）
│   ├── realtime/
│   │   ├── engine.py          # 规则匹配 + 优先级队列
│   │   ├── voice.py           # TTS 抽象（edge-tts / pyttsx3）
│   │   ├── rules_loader.py    # YAML → 规则对象
│   │   └── builtin_rules/     # 内置规则函数（when 表达式无法表达的复杂逻辑）
│   ├── collector/
│   │   ├── opendota.py        # API client
│   │   └── job.py             # 触发拉取 + 落库
│   ├── analysis/
│   │   ├── differ.py          # 赢/输局差异统计
│   │   ├── llm.py             # Claude API 综合
│   │   └── report.py          # markdown 渲染
│   ├── tasks/
│   │   ├── tracker.py         # 任务进度追踪
│   │   └── linker.py          # 任务 ↔ 实时规则联动
│   ├── db/
│   │   ├── schema.sql
│   │   └── dao.py
│   └── notify/
│       └── feishu.py          # webhook 推送
├── data/
│   ├── coach.db
│   └── reports/
├── scripts/
│   ├── install_gsi.py         # 自动找 Dota 目录、放 GSI cfg
│   └── run_weekly.py          # 手动触发周复盘的入口
└── tests/
    ├── test_gsi/
    ├── test_realtime/
    ├── test_analysis/
    └── fixtures/              # mock GSI 数据 + sample matches
```

## 9. 安装与使用

### 一次性配置

1. Steam → Dota 2 → 属性 → 启动选项添加：`-gamestateintegration -condebug`
2. `git clone` + `uv sync`
3. `uv run dotacoach install-gsi`（自动定位 Dota 目录、放置 GSI cfg）
4. 编辑 `config/settings.yaml`：填入 Steam 32 位 ID（OpenDota 用的格式，可在个人资料 URL 中找到，等于 64 位 ID 减 76561197960265728）、Anthropic API key、飞书 webhook URL
5. （Mac）`launchctl` 注册常驻 / （Win）任务计划程序注册开机启动

### 日常运行

- 实时层：开机自启常驻，监听 GSI 端口
- 复盘层：APScheduler 每周日凌晨 03:00 自动触发
- 手动触发周报告：`uv run dotacoach weekly --week 2026-W20`

## 10. 隐私与成本

- **全本地运行**，无云端用户数据存储
- **外联仅两个**：OpenDota API（公开数据）、Anthropic API（每周一次）
- **Claude 成本估算**：每周 1 次调用，启用 Prompt Caching，预计月成本 < $1
- **Steam ID 仅在本地配置文件**，不上报任何第三方

## 11. 风险与应对

| 风险 | 应对 |
|---|---|
| GSI 偶发不发包 | 心跳检测，超时记日志，不影响复盘层 |
| OpenDota API 短暂不可用 | 重试 + 本地缓存，下次跑批补 |
| Claude API 成本不可控 | 仅周报告调用，Prompt Caching 缓存 system prompt |
| 语音播报过吵 | 默认仅启用 10 条核心规则，全局 mute 热键，按规则可单独 disable |
| Console log 文件不断增长 | 仅 tail 不全量读，定期校验 Dota 自身的 log rotation |
| 隐私担忧 | 全本地、配置文件不入 git（gitignore） |
| Windows 路径/权限 | 用 pathlib + vdf 库自动探测 Steam 安装路径 |

## 12. 后续可扩展（不在本次范围）

- 本地 replay 深度解析（clarity/manta，拿到位置时间序列）
- HTML dashboard（替代 markdown）
- 对话式问答接口（"今天这局我中期是不是太保守"）
- 每英雄定制规则集
- 实时屏幕 OCR 兜底（处理 GSI 不覆盖的场景）

---

**接下来**：基于本 spec 编写实施计划（拆解为有序任务清单），交由 writing-plans skill 处理。
