# Dota Coach

Personal Dota 2 coach. Realtime advice during games + weekly blind-spot
analysis.

See [设计文档](docs/specs/2026-05-15-dota-coach-design.md) for the full design.

## Install

```bash
uv venv
uv pip install -e ".[dev]"
uv run dotacoach init
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
