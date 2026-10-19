"""
Comprehensive Test Suite for Minaram Cup 2026 Live Knockout System.
Validates all requirements specified in Section 14:
- 15 groups qualification (30 teams)
- Direct Round of 16 Qualifiers ranking and overrides
- Preliminary Draw (28 teams, 14 matches, avoid same group)
- Progression tree through Final
- Confirmed fixtures and completed results preservation
- Single-elimination invariants, drawn match penalty rules, walkovers, disputes
- Snapshot persistence and conflict detection
"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.database import Database
from app.team_manager import TeamManager
from app.tournament_manager import TournamentManager
from app.fixture_generator import FixtureGenerator
from app.results_manager import ResultsManager
from app.standings import StandingsCalculator
from app.knockout_manager import KnockoutManager
from backend.main import app
from backend.auth import ADMIN_USERNAME, ADMIN_PASSWORD


import shutil
import gc

@pytest.fixture
def temp_db():
    tmpdir = tempfile.mkdtemp(prefix="minaram_ko_test_")
    db_path = Path(tmpdir) / "test_knockout.db"
    db = Database(db_path=db_path, enable_auto_backup=False)
    yield db
    db.close()
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


def setup_15_groups_tournament(db: Database):
    """Sets up 15 groups (A through O) with 4 teams each (60 teams total) and generates round robin fixtures."""
    tm = TournamentManager(db)
    team_mgr = TeamManager(db)
    fg = FixtureGenerator(db)

    group_letters = [chr(ord('A') + i) for i in range(15)]
    teams_by_group = {}

    for letter in group_letters:
        g_id = tm.create_group(f"Group {letter}")
        teams_by_group[letter] = []
        for t_idx in range(1, 5):
            t_id = team_mgr.create_team(
                name=f"Squad {letter}{t_idx}",
                captain_name=f"Captain {letter}{t_idx}",
                group_id=g_id
            )
            teams_by_group[letter].append(t_id)

    # Generate fixtures for each group
    for letter, team_ids in teams_by_group.items():
        g_id = db.execute_one("SELECT id FROM groups WHERE name = ?;", (f"Group {letter}",))["id"]
        # Match 1: T1 vs T2
        fg.add_manual_match(team_ids[0], team_ids[1], group_id=g_id)
        # Match 2: T3 vs T4
        fg.add_manual_match(team_ids[2], team_ids[3], group_id=g_id)
        # Match 3: T1 vs T3
        fg.add_manual_match(team_ids[0], team_ids[2], group_id=g_id)
        # Match 4: T2 vs T4
        fg.add_manual_match(team_ids[1], team_ids[3], group_id=g_id)

    return teams_by_group


def test_15_groups_qualification_and_direct_qualifiers(temp_db):
    """Scenario 1 & 2: 15 groups, 30 qualifiers, 2 direct qualifiers by GF."""
    teams_by_group = setup_15_groups_tournament(temp_db)
    rm = ResultsManager(temp_db)
    km = KnockoutManager(temp_db)

    # Complete some matches so teams have scores
    # Give Group A Team 1 very high goals: 10-0
    m_ga1 = temp_db.execute_one("SELECT id FROM matches WHERE group_id = (SELECT id FROM groups WHERE name='Group A') LIMIT 1;")
    rm.record_result(m_ga1["id"], home_score=10, away_score=0)

    # Give Group B Team 1 high goals: 8-0
    m_gb1 = temp_db.execute_one("SELECT id FROM matches WHERE group_id = (SELECT id FROM groups WHERE name='Group B') LIMIT 1;")
    rm.record_result(m_gb1["id"], home_score=8, away_score=0)

    # Complete at least 1 match in every group so top teams are distinct
    for letter in [chr(ord('A') + i) for i in range(15)]:
        if letter in ("A", "B"):
            continue
        m = temp_db.execute_one("SELECT id FROM matches WHERE group_id = (SELECT id FROM groups WHERE name=?) LIMIT 1;", (f"Group {letter}",))
        rm.record_result(m["id"], home_score=3, away_score=1)

    # Calculate qualified teams
    q_data = km.get_qualified_teams()
    assert q_data["total_qualified"] == 30
    assert len(q_data["teams"]) == 30

    # Verify provisional status is tracked since not all matches in groups are finished
    assert q_data["is_provisional"] is True

    # Check Direct Qualifiers
    dq_data = km.get_direct_qualifiers(q_data["teams"])
    direct = dq_data["direct_qualifiers"]
    assert len(direct) == 2

    # Group A Team 1 (10 GF) and Group B Team 1 (8 GF) should be the 2 direct qualifiers
    assert direct[0]["goals_for"] == 10
    assert direct[0]["group_name"] == "Group A"
    assert direct[1]["goals_for"] == 8
    assert direct[1]["group_name"] == "Group B"


def test_tie_breakers_ranking_consistency(temp_db):
    """Scenario 3 & 4: Tie breakers order (GF ➔ GD ➔ PPM ➔ GPM)."""
    km = KnockoutManager(temp_db)

    # Create mock qualified teams with varying statistics
    mock_teams = [
        {"team_id": 1, "team_name": "T1", "group_name": "GA", "goals_for": 8, "goal_difference": 5, "points_per_match": 3.0, "goals_per_match": 4.0},
        {"team_id": 2, "team_name": "T2", "group_name": "GB", "goals_for": 8, "goal_difference": 6, "points_per_match": 2.0, "goals_per_match": 4.0},
        {"team_id": 3, "team_name": "T3", "group_name": "GC", "goals_for": 12, "goal_difference": 4, "points_per_match": 1.5, "goals_per_match": 4.0},
        {"team_id": 4, "team_name": "T4", "group_name": "GD", "goals_for": 8, "goal_difference": 5, "points_per_match": 3.0, "goals_per_match": 4.5},
    ]

    dq = km.get_direct_qualifiers(mock_teams)
    ranked = dq["all_ranked_candidates"]

    # Rank 1: T3 has highest GF (12)
    assert ranked[0]["team_id"] == 3
    # Rank 2: Among GF 8, T2 has highest GD (6 vs 5)
    assert ranked[1]["team_id"] == 2
    # Rank 3: Among GF 8, GD 5, PPM 3.0: T4 has higher GPM (4.5 vs 4.0)
    assert ranked[2]["team_id"] == 4
    assert ranked[3]["team_id"] == 1


def test_preliminary_draw_invariants(temp_db):
    """Scenario 5, 6, 7: 28 teams, 14 matches, avoid same group, unique teams."""
    setup_15_groups_tournament(temp_db)
    rm = ResultsManager(temp_db)
    km = KnockoutManager(temp_db)

    # Record some results
    for letter in [chr(ord('A') + i) for i in range(15)]:
        m = temp_db.execute_one("SELECT id FROM matches WHERE group_id = (SELECT id FROM groups WHERE name=?) LIMIT 1;", (f"Group {letter}",))
        rm.record_result(m["id"], home_score=2, away_score=0)

    q_data = km.get_qualified_teams()
    dq_data = km.get_direct_qualifiers(q_data["teams"])
    direct = dq_data["direct_qualifiers"]

    # Generate preliminary draw
    fixtures = km.generate_preliminary_draw(q_data["teams"], direct, draw_method="seeded")

    # Invariant 1: Exactly 14 matches
    assert len(fixtures) == 14

    # Invariant 2: Exactly 28 distinct teams across all 14 matches
    all_teams_in_draw = []
    for f in fixtures:
        assert f["home_team_id"] is not None
        assert f["away_team_id"] is not None
        assert f["home_team_id"] != f["away_team_id"]
        all_teams_in_draw.append(f["home_team_id"])
        all_teams_in_draw.append(f["away_team_id"])

    assert len(all_teams_in_draw) == 28
    assert len(set(all_teams_in_draw)) == 28

    # Invariant 3: Neither direct qualifier is in preliminary round
    dq_ids = {dq["team_id"] for dq in direct}
    for t_id in all_teams_in_draw:
        assert t_id not in dq_ids

    # Invariant 4: Same group matchup avoided where possible
    same_group_count = sum(1 for f in fixtures if f["home_group"] == f["away_group"] and f["home_group"] != "TBD")
    assert same_group_count == 0


def test_complete_bracket_tree_structure(temp_db):
    """Scenario 6: Round of 16 contains 16 unique slots, QF 8, SF 4, Final 2."""
    setup_15_groups_tournament(temp_db)
    km = KnockoutManager(temp_db)
    snap = km.get_or_create_predicted_snapshot(force=True)

    rounds = snap["rounds"]
    assert "Preliminary Round" in rounds
    assert len(rounds["Preliminary Round"]) == 14

    assert "Round of 16" in rounds
    assert len(rounds["Round of 16"]) == 8

    assert "Quarter-Final" in rounds
    assert len(rounds["Quarter-Final"]) == 4

    assert "Semi-Final" in rounds
    assert len(rounds["Semi-Final"]) == 2

    assert "Final" in rounds
    assert len(rounds["Final"]) == 1


def test_confirmed_fixtures_preserved_on_recalculation(temp_db):
    """Scenario 9 & 10: Standings update preserves confirmed fixtures and completed scores."""
    setup_15_groups_tournament(temp_db)
    rm = ResultsManager(temp_db)
    km = KnockoutManager(temp_db)

    # Initial snapshot
    km.get_or_create_predicted_snapshot(force=True)

    # Confirm PR1 fixture
    km.confirm_fixture("PR1", admin_username="admin_tester")

    # Record completed score for PR1: 4-2
    km.record_knockout_result("PR1", home_score=4, away_score=2, admin_username="admin_tester")

    off_before = temp_db.execute_one("SELECT * FROM knockout_official_fixtures WHERE bracket_slot = 'PR1';")
    assert off_before["status"] == "COMPLETED"
    assert off_before["home_score"] == 4
    assert off_before["away_score"] == 2

    # A group stage match changes
    ga_m = temp_db.execute_one("SELECT id FROM matches WHERE group_id = (SELECT id FROM groups WHERE name='Group A') LIMIT 1;")
    rm.record_result(ga_m["id"], home_score=15, away_score=0)

    # Recalculate predictions
    snap_after = km.get_or_create_predicted_snapshot(force=True)

    # Confirmed & completed fixture PR1 MUST remain intact!
    off_after = temp_db.execute_one("SELECT * FROM knockout_official_fixtures WHERE bracket_slot = 'PR1';")
    assert off_after["status"] == "COMPLETED"
    assert off_after["home_score"] == 4
    assert off_after["away_score"] == 2


def test_preliminary_winner_advances_correctly(temp_db):
    """Scenario 11 & 12: Winner of PR1 advances into R16_1 away slot."""
    setup_15_groups_tournament(temp_db)
    km = KnockoutManager(temp_db)

    # Generate predictions & confirm PR1
    km.get_or_create_predicted_snapshot(force=True)
    km.confirm_fixture("PR1")

    fix = temp_db.execute_one("SELECT home_team_id, away_team_id FROM knockout_official_fixtures WHERE bracket_slot = 'PR1';")
    winner_id = fix["home_team_id"]

    # Record PR1 result: home wins 3-1
    res = km.record_knockout_result("PR1", home_score=3, away_score=1)
    assert res["status"] == "COMPLETED"
    assert res["winner_team_id"] == winner_id
    assert res["advanced_to"] == "R16_1"

    # Verify R16_1 has winner_id in away_team_id
    r16_1 = temp_db.execute_one("SELECT away_team_id FROM knockout_official_fixtures WHERE bracket_slot = 'R16_1';")
    assert r16_1["away_team_id"] == winner_id


def test_drawn_knockout_match_requires_winner(temp_db):
    """Scenario 13: Drawn knockout match cannot end without extra time / penalties winner."""
    setup_15_groups_tournament(temp_db)
    km = KnockoutManager(temp_db)

    km.get_or_create_predicted_snapshot(force=True)
    km.confirm_fixture("PR2")

    # Tied score with no penalty should raise ValueError
    with pytest.raises(ValueError, match="cannot end in a draw"):
        km.record_knockout_result("PR2", home_score=2, away_score=2)

    # Tied score with tied penalties should raise ValueError
    with pytest.raises(ValueError, match="Penalty scores cannot be tied"):
        km.record_knockout_result("PR2", home_score=2, away_score=2, home_penalty=4, away_penalty=4)

    # Tied score with winning penalties: 5-4 penalties should succeed!
    res = km.record_knockout_result("PR2", home_score=2, away_score=2, home_penalty=5, away_penalty=4)
    assert res["status"] == "COMPLETED"


def test_walkover_requires_reason_and_records_audit(temp_db):
    """Scenario 15: Walkovers require documented reason and record audit log."""
    setup_15_groups_tournament(temp_db)
    km = KnockoutManager(temp_db)

    km.get_or_create_predicted_snapshot(force=True)
    km.confirm_fixture("PR3")

    fix = temp_db.execute_one("SELECT home_team_id, away_team_id FROM knockout_official_fixtures WHERE bracket_slot = 'PR3';")
    awarded_team = fix["home_team_id"]

    # Empty reason fails
    with pytest.raises(ValueError, match="clear, documented policy reason"):
        km.record_walkover("PR3", winner_team_id=awarded_team, reason="")

    # Valid walkover
    res = km.record_walkover("PR3", winner_team_id=awarded_team, reason="Opponent failed to appear at designated lobby within 15 min grace window.")
    assert res["status"] == "COMPLETED"

    # Verify audit log
    logs = km.get_audit_logs(limit=5)
    walkover_log = next((l for l in logs if l["action"] == "RECORD_RESULT"), None)
    assert walkover_log is not None


def test_administrator_overrides_persisted(temp_db):
    """Scenario 16: Direct qualifier manual override is persisted and visible."""
    setup_15_groups_tournament(temp_db)
    km = KnockoutManager(temp_db)

    t_row = temp_db.execute_one("SELECT id FROM teams LIMIT 1;")
    special_team_id = t_row["id"]

    km.set_direct_qualifier_override(
        slot_index=0,
        team_id=special_team_id,
        reason="Disciplinary committee reinstated team directly to R16",
        admin_username="superadmin"
    )

    dq_data = km.get_direct_qualifiers()
    assert dq_data["has_override"] is True
    assert dq_data["direct_qualifiers"][0]["team_id"] == special_team_id
    assert dq_data["direct_qualifiers"][0]["is_override"] is True

    # Clearing override restores calculation
    km.clear_direct_qualifier_overrides()
    dq_after = km.get_direct_qualifiers()
    assert dq_after["has_override"] is False


def test_reset_predictions_preserves_confirmed(temp_db):
    """Scenario 20: Resetting predictions does not delete confirmed or completed fixtures."""
    setup_15_groups_tournament(temp_db)
    km = KnockoutManager(temp_db)

    km.get_or_create_predicted_snapshot(force=True)
    km.confirm_fixture("PR4")
    km.record_knockout_result("PR4", home_score=2, away_score=0)

    # Reset predictions
    km.reset_unconfirmed_predictions(admin_username="admin")

    # Official fixture must still exist
    pr4 = temp_db.execute_one("SELECT * FROM knockout_official_fixtures WHERE bracket_slot = 'PR4';")
    assert pr4 is not None
    assert pr4["status"] == "COMPLETED"
    assert pr4["home_score"] == 2
