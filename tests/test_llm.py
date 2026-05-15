import json
from unittest.mock import MagicMock, AsyncMock

from dotacoach.analysis.llm import generate_report
from dotacoach.analysis.differ import Difference
from dotacoach.analysis.llm_models import LlmReport


async def test_generate_report_calls_claude_with_caching(monkeypatch):
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text=json.dumps({
        "patterns": [{"title": "t", "evidence": "e", "hypothesis": "h", "verification": "v"}],
        "tasks": [{"description": "d", "metric": "vision.wards_per_game",
                   "target": 5, "direction": ">=", "linked_rule_ids": []}],
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
