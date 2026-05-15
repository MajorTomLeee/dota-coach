from pathlib import Path
from dotacoach.consolelog.parser import parse_line

def test_parse_ability_cast():
    e = parse_line("00:11:45 npc_dota_hero_lion cast lion_finger_of_death")
    assert e is not None
    assert e.type == "log.enemy_cast"
    assert e.payload["hero"] == "npc_dota_hero_lion"
    assert e.payload["ability"] == "lion_finger_of_death"
    assert e.payload["game_time"] == 11 * 60 + 45

def test_parse_purchase():
    e = parse_line("00:12:00 npc_dota_hero_pudge purchased item_tpscroll")
    assert e.type == "log.purchase"
    assert e.payload["item"] == "item_tpscroll"

def test_unrecognized_returns_none():
    assert parse_line("[Steam] random line") is None
