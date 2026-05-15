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
