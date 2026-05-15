from dotacoach.analysis.differ import hero_pool_stats
from dotacoach.analysis.loader import MatchRecord


def make(hero, win):
    return MatchRecord(match_id=1, hero_id=hero, win=win, duration=2000,
                       player={})


def test_hero_pool_winrate():
    matches = [make(14, True), make(14, False), make(14, False),
               make(1, True), make(1, True)]
    stats = hero_pool_stats(matches)
    pudge = next(s for s in stats if s["hero_id"] == 14)
    assert pudge["games"] == 3
    assert pudge["wins"] == 1
    aa = next(s for s in stats if s["hero_id"] == 1)
    assert aa["winrate"] == 1.0
