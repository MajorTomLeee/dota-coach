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
