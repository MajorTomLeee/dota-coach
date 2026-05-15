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
