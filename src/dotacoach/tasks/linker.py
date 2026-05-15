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
            out.append(
                r.model_copy(
                    update={
                        "priority": "critical",
                        "cooldown_s": max(5, r.cooldown_s // 2),
                    }
                )
            )
        else:
            out.append(r)
    return out
