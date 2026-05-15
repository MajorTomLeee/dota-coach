from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from scipy import stats

from .loader import MatchRecord


@dataclass
class Difference:
    metric: str
    win_mean: float
    loss_mean: float
    p_value: float
    direction: str  # "win_higher" | "loss_higher"
    significant: bool


def _safe_get(timeseries: list[int] | None, idx: int) -> float | None:
    if not timeseries or idx >= len(timeseries):
        return None
    return float(timeseries[idx])


def _series_at(records: Iterable[MatchRecord], field: str, minute: int
               ) -> list[float]:
    out = []
    for r in records:
        v = _safe_get(r.player.get(field), minute)
        if v is not None:
            out.append(v)
    return out


def _stat_diff(metric: str, w_vals: list[float], l_vals: list[float],
               p_threshold: float = 0.1) -> Difference | None:
    if len(w_vals) < 2 or len(l_vals) < 2:
        return None
    w_mean, l_mean = mean(w_vals), mean(l_vals)
    if w_mean == l_mean:
        p = 1.0
    else:
        try:
            p = float(stats.ttest_ind(w_vals, l_vals, equal_var=False).pvalue)
        except Exception:
            p = 1.0
    return Difference(
        metric=metric, win_mean=w_mean, loss_mean=l_mean, p_value=p,
        direction="win_higher" if w_mean > l_mean else "loss_higher",
        significant=p < p_threshold,
    )


def compute_differences(wins: list[MatchRecord], losses: list[MatchRecord]
                        ) -> list[Difference]:
    out: list[Difference] = []
    for minute in (5, 10, 15, 20):
        for field, label in [("gold_t", "gold_at"), ("xp_t", "xp_at"),
                             ("lh_t", "lh_at")]:
            d = _stat_diff(
                f"{label}_{minute}min",
                _series_at(wins, field, minute),
                _series_at(losses, field, minute),
            )
            if d:
                out.append(d)

    for fld in ["kills", "deaths", "assists", "gold_per_min", "xp_per_min"]:
        d = _stat_diff(
            fld,
            [r.player.get(fld, 0) for r in wins],
            [r.player.get(fld, 0) for r in losses],
        )
        if d:
            out.append(d)
    return out


def hero_pool_stats(matches: list[MatchRecord]) -> list[dict]:
    by_hero: dict[int, dict] = {}
    for r in matches:
        agg = by_hero.setdefault(r.hero_id, {"hero_id": r.hero_id, "games": 0, "wins": 0})
        agg["games"] += 1
        if r.win:
            agg["wins"] += 1
    out = []
    for agg in by_hero.values():
        agg["winrate"] = agg["wins"] / agg["games"]
        out.append(agg)
    out.sort(key=lambda x: -x["games"])
    return out
