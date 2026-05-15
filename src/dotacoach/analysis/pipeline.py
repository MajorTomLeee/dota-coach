import time

from anthropic import AsyncAnthropic

from dotacoach.db.dao import Database
from dotacoach.tasks.tracker import TaskTracker

from .differ import compute_differences, hero_pool_stats
from .llm import generate_report
from .llm_models import LlmReport
from .loader import load_split
from .report import render_markdown


async def run_weekly_pipeline(
    db: Database,
    account_id: int,
    week_label: str,
    anthropic_client: AsyncAnthropic,
    model: str,
    since_ts: int,
) -> tuple[str, LlmReport]:
    wins, losses = load_split(db, account_id, since_ts)
    diffs = compute_differences(wins, losses)
    pool = hero_pool_stats(wins + losses)

    # 上周任务自动 finalize（actuals 用空字典 → completed=None；后续可加真正测算）
    tracker = TaskTracker(db)
    previous = tracker.finalize_week(_previous_week_label(week_label), actuals={})

    report = await generate_report(
        client=anthropic_client,
        model=model,
        diffs=diffs,
        hero_pool=pool,
        previous_tasks=previous,
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
        return f"{int(year) - 1}-W52"
    return f"{year}-W{n:02d}"
