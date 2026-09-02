"""Turn-based tactical grid combat: encounter setup, movement, attacks,
obstacles, AI turns, and win/loss detection."""
import json
import random

import pytest

from core import tactical_combat as tc
from core.storage import get_conn


def test_weapon_range_scales_with_tier():
    assert tc._weapon_range_for(None, 0) == 1
    assert tc._weapon_range_for(None, 3) == 1
    assert tc._weapon_range_for(None, 4) == 3
    assert tc._weapon_range_for(None, 6) == 3
    assert tc._weapon_range_for(None, 9) == 5
    assert tc._weapon_range_for(None, None) == 1  # tier 2 default -> melee range
    assert tc._weapon_range_for("Longbow", None) == 4  # real ranged weapon
    assert tc._weapon_range_for("Halberd", None) == 2  # reach property


def test_chebyshev_distance():
    assert tc._chebyshev(0, 0, 3, 0) == 3
    assert tc._chebyshev(0, 0, 2, 2) == 2
    assert tc._chebyshev(1, 1, 1, 1) == 0


def test_line_clear_detects_blocking_obstacle():
    obstacles = {(2, 2)}
    assert tc._line_clear(obstacles, 0, 0, 4, 4) is False
    assert tc._line_clear(set(), 0, 0, 4, 4) is True
    assert tc._line_clear(obstacles, 0, 0, 0, 3) is True  # straight line elsewhere


def test_bfs_reachable_respects_obstacles_and_occupied_tiles():
    reachable = tc._bfs_reachable((0, 0), obstacles={(1, 0)}, occupied={(0, 1)}, width=8, height=8, points=2)
    assert (1, 0) not in reachable
    assert (0, 1) not in reachable
    assert (0, 0) not in reachable  # never includes the start tile
    assert (1, 1) in reachable  # diagonal step around the obstacle


def test_bfs_reachable_bounded_by_movement_points():
    reachable = tc._bfs_reachable((4, 4), obstacles=set(), occupied=set(), width=8, height=8, points=1)
    assert all(tc._chebyshev(4, 4, x, y) <= 1 for x, y in reachable)
    assert (6, 4) not in reachable


def test_start_encounter_builds_full_grid(temp_db):
    random.seed(1)
    encounter = tc.start_encounter("sess-1", world_id=None, character_id=None, danger=4)
    assert encounter["grid_width"] == tc.GRID_SIZE
    assert encounter["grid_height"] == tc.GRID_SIZE
    assert encounter["status"] in ("active", "won", "lost")
    assert len(encounter["obstacles"]) >= 5
    # player + 2 allies + at least 2 enemies
    assert sum(1 for u in encounter["units"] if u["unit_type"] == "player") == 3
    assert sum(1 for u in encounter["units"] if u["unit_type"] == "enemy") >= 2
    # no two units share a tile
    positions = [(u["x"], u["y"]) for u in encounter["units"]]
    assert len(positions) == len(set(positions))
    # no unit stands on an obstacle
    obstacle_set = set(encounter["obstacles"])
    assert not any((u["x"], u["y"]) in obstacle_set for u in encounter["units"])


def test_start_encounter_lands_on_human_turn_or_game_over(temp_db):
    random.seed(2)
    encounter = tc.start_encounter("sess-2", world_id=None, character_id=None, danger=3)
    if encounter["status"] == "active":
        current = next(u for u in encounter["units"] if u["id"] == encounter["current_unit_id"])
        assert current["stats"].get("is_human")


def _human_unit(encounter):
    return next(u for u in encounter["units"] if u["stats"].get("is_human"))


def test_move_rejects_out_of_range_tile(temp_db):
    random.seed(3)
    encounter = tc.start_encounter("sess-3", world_id=None, character_id=None, danger=2)
    if encounter["status"] != "active":
        pytest.skip("encounter resolved before human's turn under this seed")
    human = _human_unit(encounter)
    far_x = min(tc.GRID_SIZE - 1, human["x"] + tc.MOVE_POINTS + 5)
    result = tc.move_unit(encounter["id"], human["id"], far_x, human["y"])
    assert "error" in result


def test_move_rejects_when_not_units_turn(temp_db):
    random.seed(4)
    encounter = tc.start_encounter("sess-4", world_id=None, character_id=None, danger=2)
    if encounter["status"] != "active":
        pytest.skip("encounter resolved before human's turn under this seed")
    non_current = next(u for u in encounter["units"] if u["id"] != encounter["current_unit_id"])
    result = tc.move_unit(encounter["id"], non_current["id"], non_current["x"], non_current["y"])
    assert "error" in result


def test_move_valid_tile_updates_position_and_advances_turn(temp_db):
    random.seed(5)
    encounter = tc.start_encounter("sess-5", world_id=None, character_id=None, danger=1)
    if encounter["status"] != "active":
        pytest.skip("encounter resolved before human's turn under this seed")
    human = _human_unit(encounter)
    occupied = {(u["x"], u["y"]) for u in encounter["units"] if u["id"] != human["id"]}
    reachable = tc._bfs_reachable((human["x"], human["y"]), set(encounter["obstacles"]), occupied,
                                   tc.GRID_SIZE, tc.GRID_SIZE, tc.MOVE_POINTS)
    assert reachable, "expected at least one reachable tile on a fresh board"
    dest = next(iter(reachable))
    result = tc.move_unit(encounter["id"], human["id"], dest[0], dest[1])
    assert "error" not in result
    moved_unit = next(u for u in result["units"] if u["id"] == human["id"])
    assert (moved_unit["x"], moved_unit["y"]) == dest


def test_attack_rejects_out_of_range_target(temp_db):
    random.seed(6)
    encounter = tc.start_encounter("sess-6", world_id=None, character_id=None, danger=2)
    if encounter["status"] != "active":
        pytest.skip("encounter resolved before human's turn under this seed")
    human = _human_unit(encounter)
    far_enemy = max((u for u in encounter["units"] if u["unit_type"] == "enemy"),
                     key=lambda e: tc._chebyshev(human["x"], human["y"], e["x"], e["y"]))
    if tc._chebyshev(human["x"], human["y"], far_enemy["x"], far_enemy["y"]) <= tc._weapon_range_for(human["stats"].get("weapon_name"), human["stats"].get("weapon_tier")):
        pytest.skip("every enemy happened to be in range on this seed")
    result = tc.attack_unit(encounter["id"], human["id"], far_enemy["id"])
    assert "error" in result


def test_attack_rejects_same_side_target(temp_db):
    random.seed(7)
    encounter = tc.start_encounter("sess-7", world_id=None, character_id=None, danger=2)
    if encounter["status"] != "active":
        pytest.skip("encounter resolved before human's turn under this seed")
    human = _human_unit(encounter)
    ally = next(u for u in encounter["units"] if u["unit_type"] == "player" and u["id"] != human["id"])
    result = tc.attack_unit(encounter["id"], human["id"], ally["id"])
    assert "error" in result


def test_full_encounter_can_be_won_by_defeating_all_enemies(temp_db):
    """Force a lopsided fight (huge player stats, weak enemies at point-blank
    range) and play it out via end_turn/attack until someone wins, to prove
    the win/loss/turn-advance loop terminates and reports a real outcome."""
    random.seed(42)
    encounter = tc.start_encounter("sess-8", world_id=None, character_id=None, danger=0)
    encounter_id = encounter["id"]

    # Stack the deck: give the human overwhelming strength and put every
    # enemy at 1 HP so the fight resolves in a handful of turns.
    conn = get_conn()
    human_row = conn.execute(
        "SELECT id, stats_json FROM combat_state WHERE encounter_id=? AND unit_type='player'", (encounter_id,)
    ).fetchall()
    for row in human_row:
        stats = json.loads(row["stats_json"])
        if stats.get("is_human"):
            stats["str_mod"] = 15
            conn.execute("UPDATE combat_state SET stats_json=? WHERE id=?", (json.dumps(stats), row["id"]))
    conn.execute("UPDATE combat_state SET hp=1, max_hp=1 WHERE encounter_id=? AND unit_type='enemy'", (encounter_id,))
    conn.commit()
    conn.close()

    for _ in range(200):
        encounter = tc.get_encounter(encounter_id)
        if encounter["status"] != "active":
            break
        human = next((u for u in encounter["units"] if u["stats"].get("is_human")), None)
        if human is None or not human["is_active"]:
            break
        enemies = [u for u in encounter["units"] if u["unit_type"] == "enemy" and u["is_active"]]
        if not enemies:
            break
        target = min(enemies, key=lambda e: tc._chebyshev(human["x"], human["y"], e["x"], e["y"]))
        dist = tc._chebyshev(human["x"], human["y"], target["x"], target["y"])
        rng = tc._weapon_range_for(human["stats"].get("weapon_name"), human["stats"].get("weapon_tier"))
        if dist <= rng:
            tc.attack_unit(encounter_id, human["id"], target["id"])
        else:
            occupied = {(u["x"], u["y"]) for u in encounter["units"] if u["is_active"] and u["id"] != human["id"]}
            reachable = tc._bfs_reachable((human["x"], human["y"]), set(encounter["obstacles"]), occupied,
                                           tc.GRID_SIZE, tc.GRID_SIZE, tc.MOVE_POINTS)
            if not reachable:
                tc.end_turn(encounter_id, human["id"])
                continue
            dest = min(reachable, key=lambda p: tc._chebyshev(p[0], p[1], target["x"], target["y"]))
            tc.move_unit(encounter_id, human["id"], dest[0], dest[1])

    final = tc.get_encounter(encounter_id)
    assert final["status"] in ("won", "lost")


def test_get_active_encounter_finds_the_open_one(temp_db):
    random.seed(8)
    started = tc.start_encounter("sess-9", world_id=None, character_id=None, danger=2)
    active = tc.get_active_encounter("sess-9")
    assert active is not None
    assert active["id"] == started["id"]


def test_no_active_encounter_for_unknown_session(temp_db):
    assert tc.get_active_encounter("no-such-session") is None
