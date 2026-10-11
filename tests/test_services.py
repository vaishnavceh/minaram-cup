"""
Comprehensive test suite for all Minaram Cup tournament management services.
Uses temporary SQLite database to avoid touching real tournament data.
"""

import tempfile
from pathlib import Path
import pytest

from app.database import Database
from app.models import Registration, Team, TournamentSettings
from app.registration_parser import parse_registration_text
from app.registration_service import RegistrationService
from app.team_manager import TeamManager
from app.tournament_manager import TournamentManager
from app.fixture_generator import FixtureGenerator
from app.standings import StandingsCalculator
from app.knockout_manager import KnockoutManager
from app.results_manager import ResultsManager
from app.export_service import ExportService
from app.backup_service import BackupService


import shutil
import gc

@pytest.fixture
def temp_db():
    tmpdir = tempfile.mkdtemp(prefix="minaram_test_")
    db_path = Path(tmpdir) / "test_minaram.db"
    db = Database(db_path=db_path)
    yield db
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_database_persistence(temp_db):
    temp_db.set_setting("test_key", "hello_world")
    assert temp_db.get_setting("test_key") == "hello_world"

    # Reopen database connection
    db_reopened = Database(db_path=temp_db.db_path)
    assert db_reopened.get_setting("test_key") == "hello_world"


def test_registration_service_and_duplicates(temp_db):
    reg_service = RegistrationService(temp_db)

    # Preview and save
    text = """
    Name: Vaishnav
    Phone No: 9746603975
    Team Name: Binladen Fc
    """
    previews = reg_service.preview_raw_text(text)
    assert len(previews) == 1
    assert previews[0]["duplicate_status"] == "Unique"

    saved_count, errors = reg_service.save_parsed_registrations(previews, auto_confirm=True)
    assert saved_count == 1
    assert len(errors) == 0

    # Test duplicate detection on second paste
    dup_previews = reg_service.preview_raw_text(text)
    assert len(dup_previews) == 1
    assert "Duplicate" in dup_previews[0]["duplicate_status"]

    regs = reg_service.get_registrations()
    assert len(regs) == 1
    assert regs[0].participant_name == "Vaishnav"
    assert regs[0].phone_number == "9746603975"


def test_team_manager_crud_and_merge(temp_db):
    tm = TeamManager(temp_db)
    t1_id = tm.create_team(name="Binladen Fc", captain_name="Vaishnav", phone_number="9746603975")
    t2_id = tm.create_team(name="Binladen Juniors", captain_name="Arjun", phone_number="9876543210")

    teams = tm.get_teams()
    assert len(teams) == 2

    # Cannot create duplicate team name
    with pytest.raises(ValueError):
        tm.create_team(name="binladen fc")

    # Merge t2 into t1
    success, msg = tm.merge_teams(source_team_id=t2_id, target_team_id=t1_id)
    assert success is True
    assert len(tm.get_teams()) == 1


def test_group_distribution_and_randomization(temp_db):
    tourn_mgr = TournamentManager(temp_db)
    tm = TeamManager(temp_db)

    tourn_mgr.create_group("Group A")
    tourn_mgr.create_group("Group B")

    for i in range(1, 9):
        tm.create_team(name=f"Team {i}", seed=1 if i <= 2 else 0)

    # Preview distribution with real randomization
    alloc = tourn_mgr.preview_team_distribution(randomize=True, seed_aware=True)
    assert "Group A" in alloc and "Group B" in alloc
    assert len(alloc["Group A"]) == 4
    assert len(alloc["Group B"]) == 4

    tourn_mgr.apply_group_allocation(alloc)
    g_a_teams = tourn_mgr.get_group_teams(1)
    g_b_teams = tourn_mgr.get_group_teams(2)
    assert len(g_a_teams) == 4
    assert len(g_b_teams) == 4


def test_round_robin_fixture_generation(temp_db):
    fg = FixtureGenerator(temp_db)

    # Even count (4 teams) -> 3 rounds, 6 total matches
    teams_4 = [{"id": 1, "name": "T1"}, {"id": 2, "name": "T2"}, {"id": 3, "name": "T3"}, {"id": 4, "name": "T4"}]
    rounds_4 = fg.generate_round_robin_pairings(teams_4)
    assert len(rounds_4) == 3
    total_matches_4 = sum(len(r) for r in rounds_4)
    assert total_matches_4 == 6

    # Odd count (3 teams) -> with byes -> 3 rounds, 3 matches total
    teams_3 = [{"id": 1, "name": "T1"}, {"id": 2, "name": "T2"}, {"id": 3, "name": "T3"}]
    rounds_3 = fg.generate_round_robin_pairings(teams_3)
    assert len(rounds_3) == 3
    total_matches_3 = sum(len(r) for r in rounds_3)
    assert total_matches_3 == 3


def test_standings_and_tie_breakers(temp_db):
    tm = TournamentManager(temp_db)
    team_mgr = TeamManager(temp_db)
    fg = FixtureGenerator(temp_db)
    rm = ResultsManager(temp_db)
    sc = StandingsCalculator(temp_db)

    g1_id = tm.create_group("Group Alpha")
    t1 = team_mgr.create_team(name="Alpha Stars", group_id=g1_id)
    t2 = team_mgr.create_team(name="Beta Warriors", group_id=g1_id)
    t3 = team_mgr.create_team(name="Gamma Strikers", group_id=g1_id)

    # Match 1: Alpha 2 - 1 Beta
    m1 = fg.add_manual_match(t1, t2, group_id=g1_id)
    rm.record_result(m1, home_score=2, away_score=1)

    # Match 2: Alpha 3 - 0 Gamma
    m2 = fg.add_manual_match(t1, t3, group_id=g1_id)
    rm.record_result(m2, home_score=3, away_score=0)

    # Match 3: Beta 1 - 0 Gamma
    m3 = fg.add_manual_match(t2, t3, group_id=g1_id)
    rm.record_result(m3, home_score=1, away_score=0)

    standings = sc.calculate_group_standings(g1_id)
    assert len(standings) == 3

    # Alpha: 2 played, 2 won, 6 pts, GD +4
    assert standings[0].team_id == t1
    assert standings[0].played == 2
    assert standings[0].won == 2
    assert standings[0].points == 6
    assert standings[0].goal_difference == 4
    assert standings[0].is_qualified is True

    # Beta: 2 played, 1 won, 1 lost, 3 pts, GD 0
    assert standings[1].team_id == t2
    assert standings[1].points == 3
    assert standings[1].is_qualified is True

    # Gamma: 2 played, 0 won, 2 lost, 0 pts
    assert standings[2].team_id == t3
    assert standings[2].points == 0
    assert standings[2].is_qualified is False


def test_knockout_bracket_and_advancement(temp_db):
    backup_svc = BackupService(temp_db)
    backup_svc.generate_sample_tournament()

    rm = ResultsManager(temp_db)
    km = KnockoutManager(temp_db)

    # Check that semi final matches exist
    sf1 = temp_db.execute_one("SELECT id, bracket_slot, status FROM matches WHERE bracket_slot = 'SF1';")
    assert sf1 is not None

    # Get home and away team IDs for SF1
    teams = temp_db.execute_one("SELECT id, home_team_id, away_team_id FROM matches WHERE bracket_slot = 'SF1';")
    # If not assigned yet, assign them
    t_rows = temp_db.execute_query("SELECT id FROM teams LIMIT 2;")
    h_id, a_id = t_rows[0]["id"], t_rows[1]["id"]
    temp_db.execute_non_query("UPDATE matches SET home_team_id = ?, away_team_id = ? WHERE id = ?;", (h_id, a_id, sf1["id"]))

    # Play SF1: Team 1 wins 3-1
    success, msg = rm.record_result(sf1["id"], home_score=3, away_score=1)
    assert success is True

    # Final match should now have h_id in home_team_id!
    final_m = temp_db.execute_one("SELECT home_team_id FROM matches WHERE bracket_slot = 'F';")
    assert final_m["home_team_id"] == h_id

    # Verify audit trail
    audits = rm.get_audit_trail(sf1["id"])
    assert len(audits) >= 1
    assert audits[0].new_home_score == 3
    assert audits[0].new_away_score == 1


def test_exports_and_backups(temp_db):
    backup_svc = BackupService(temp_db)
    backup_svc.generate_sample_tournament()

    with tempfile.TemporaryDirectory() as outdir:
        out_path = Path(outdir)
        exp_svc = ExportService(temp_db)

        # CSV exports
        csv_reg = out_path / "regs.csv"
        exp_svc.export_registrations(csv_reg)
        assert csv_reg.exists() and csv_reg.stat().st_size > 0

        csv_fix = out_path / "fixtures.csv"
        exp_svc.export_fixtures(csv_fix)
        assert csv_fix.exists() and csv_fix.stat().st_size > 0

        # XLSX exports
        xlsx_stand = out_path / "standings.xlsx"
        exp_svc.export_standings(xlsx_stand)
        assert xlsx_stand.exists() and xlsx_stand.stat().st_size > 0

        xlsx_full = out_path / "full_tournament.xlsx"
        exp_svc.export_full_tournament_workbook(xlsx_full)
        assert xlsx_full.exists() and xlsx_full.stat().st_size > 0

        # Backup & Restore
        b_file = backup_svc.create_backup(label="test")
        assert b_file.exists() and b_file.stat().st_size > 0

        success, r_msg = backup_svc.restore_backup(b_file)
        assert success is True
