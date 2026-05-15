from .llm_models import LlmReport


def _check_mark(completed: bool | None) -> str:
    if completed is True:
        return "\u2705"
    if completed is False:
        return "\u274c"
    return "\u26a0\ufe0f"


def render_markdown(week_label: str, report: LlmReport,
                    previous_task_results: list[dict]) -> str:
    parts = [f"# Dota Coach 周报告 \u00b7 {week_label}", ""]

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
        rules = ", ".join(t.linked_rule_ids) or "\u2014"
        parts.append(
            f"{i}. {t.description}（指标 `{t.metric}` {t.direction} {t.target}；"
            f"关联规则：{rules}）"
        )

    return "\n".join(parts) + "\n"
