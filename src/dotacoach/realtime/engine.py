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
