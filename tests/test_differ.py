from dotacoach.analysis.differ import compute_differences
from dotacoach.analysis.loader import MatchRecord


def make(win, gold_t, kills=5, deaths=2):
    return MatchRecord(
        match_id=1, hero_id=14, win=win, duration=2000,
        player={
            "gold_t": gold_t, "xp_t": gold_t, "lh_t": [0] * len(gold_t),
            "dn_t": [0] * len(gold_t), "kills": kills, "deaths": deaths,
            "assists": 0, "purchase_log": [], "gold_per_min": 500,
            "xp_per_min": 600,
        }
    )


def test_gpm_at_10_difference():
    wins = [make(True, [0] + [100 * i for i in range(1, 30)]) for _ in range(3)]
    losses = [make(False, [0] + [80 * i for i in range(1, 30)]) for _ in range(3)]
    diffs = compute_differences(wins, losses)
    item = next(d for d in diffs if d.metric == "gold_at_10min")
    assert item.win_mean > item.loss_mean
    assert item.direction == "win_higher"


def test_returns_only_significant_or_large_gaps():
    wins = [make(True, [0] + [100 * i for i in range(1, 30)]) for _ in range(3)]
    losses = [make(False, [0] + [100 * i for i in range(1, 30)]) for _ in range(3)]
    diffs = compute_differences(wins, losses)
    # 完全相同的曲线 → 至少 GPM 系列不应被标记
    gpm_items = [d for d in diffs if d.metric.startswith("gold_at_")]
    assert all(not d.significant for d in gpm_items)
