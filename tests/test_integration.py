"""
End-to-end integration tests for Minaram Cup Tournament Management System.
Simulates a full tournament lifecycle from pasted registration to champion crowning.
"""

import tempfile
import shutil
import gc
from pathlib import Path
import pytest

from app.database import Database
from app.registration_service import RegistrationService
from app.team_manager import TeamManager
from app.tournament_manager import TournamentManager
from app.fixture_generator import FixtureGenerator
from app.results_manager import ResultsManager
from app.standings import StandingsCalculator
from app.knockout_manager import KnockoutManager
from app.export_service import ExportService
from app.backup_service import BackupService


@pytest.fixture
def test_env():
    tmpdir = tempfile.mkdtemp(prefix="minaram_integration_")
    db_path = Path(tmpdir) / "tournament.db"
    db = Database(db_path=db_path)
    yield db, Path(tmpdir)
    gc.collect()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_full_tournament_lifecycle(test_env):
    db, tmp_dir = test_env
    reg_svc = RegistrationService(db)
    team_mgr = TeamManager(db)
    tourn_mgr = TournamentManager(db)
    fix_gen = FixtureGenerator(db)
    res_mgr = ResultsManager(db)
    stand_calc = StandingsCalculator(db)
    ko_mgr = KnockoutManager(db)
    exp_svc = ExportService(db)
    backup_svc = BackupService(db, backup_dir=tmp_dir / "backups")

    # 1. Paste multi-registration WhatsApp block
    paste_text = r"""
    Registration Format
    Name: Vaishnav
    Phone No: 09746603975
    Team Name: Binladen Fc

    Registration Format
    Name: Arjun K
    Phone No: 9847112233
    Team Name: Red Star FC

    Name: Rayan \ Phone: 9495123456 \ Team: Coastal Kings
    Name: Farhan \ Phone: 9123456789 \ Team: Cyber Strikers
    """
    previews = reg_svc.preview_raw_text(paste_text)
    assert len(previews) == 4
    for p in previews:
        assert p["is_valid"] is True

    # 2. Save and Auto-Confirm into Teams
    saved_count, errors = reg_svc.save_parsed_registrations(previews, auto_confirm=True)
    assert saved_count == 4
    assert len(team_mgr.get_teams()) == 4

    # 3. Create Groups and Distribute
    g_a_id = tourn_mgr.create_group("Group A")
    g_b_id = tourn_mgr.create_group("Group B")

    teams = team_mgr.get_teams()
    tourn_mgr.assign_team_to_group(teams[0].id, g_a_id)
    tourn_mgr.assign_team_to_group(teams[1].id, g_a_id)
    tourn_mgr.assign_team_to_group(teams[2].id, g_b_id)
    tourn_mgr.assign_team_to_group(teams[3].id, g_b_id)

    # 4. Generate Group Stage Fixtures
    fixtures = fix_gen.preview_group_fixtures(start_date="2026-10-15", start_time="10:00")
    assert len(fixtures) == 2  # 1 match per group
    saved_f = fix_gen.save_fixtures(fixtures)
    assert saved_f == 2

    # 5. Play Matches & Record Results
    m1 = db.execute_one("SELECT id FROM matches WHERE group_id = ?;", (g_a_id,))["id"]
    m2 = db.execute_one("SELECT id FROM matches WHERE group_id = ?;", (g_b_id,))["id"]

    ok1, _ = res_mgr.record_result(m1, home_score=3, away_score=1)
    ok2, _ = res_mgr.record_result(m2, home_score=2, away_score=0)
    assert ok1 is True and ok2 is True

    # 6. Verify Standings
    standings_a = stand_calc.calculate_group_standings(g_a_id)
    assert len(standings_a) == 2
    assert standings_a[0].won == 1
    assert standings_a[0].points == 3
    assert standings_a[0].is_qualified is True

    standings_b = stand_calc.calculate_group_standings(g_b_id)
    assert len(standings_b) == 2
    assert standings_b[0].won == 1
    assert standings_b[0].points == 3
    assert standings_b[0].is_qualified is True

    # 7. Generate Knockout Bracket from Group Standings
    ko_fixtures = ko_mgr.generate_bracket_from_group_qualifiers(start_date="2026-10-16")
    assert len(ko_fixtures) == 3  # SF1, SF2, Final

    # Save knockout matches
    for f in ko_fixtures:
        db.execute_non_query("""
            INSERT INTO matches (match_number, stage, round_number, bracket_slot, home_team_id, away_team_id, scheduled_date, scheduled_time, venue, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled', ?);
        """, (f["match_number"], f["stage"], f["round_number"], f["bracket_slot"], f.get("home_team_id"), f.get("away_team_id"), f["scheduled_date"], f["scheduled_time"], f["venue"], f.get("notes", "")))

    # 8. Play Semi-Finals
    sf1 = db.execute_one("SELECT id, home_team_id, away_team_id FROM matches WHERE bracket_slot = 'SF1';")
    ok_sf1, _ = res_mgr.record_result(sf1["id"], home_score=2, away_score=0)
    assert ok_sf1 is True

    sf2 = db.execute_one("SELECT id, home_team_id, away_team_id FROM matches WHERE bracket_slot = 'SF2';")
    ok_sf2, _ = res_mgr.record_result(sf2["id"], home_score=1, away_score=0)
    assert ok_sf2 is True

    # Check Final match has advancing winners!
    final_m = db.execute_one("SELECT id, home_team_id, away_team_id FROM matches WHERE bracket_slot = 'F';")
    assert final_m["home_team_id"] == sf1["home_team_id"]
    assert final_m["away_team_id"] == sf2["home_team_id"]

    # Crown Champion in Final
    ok_f, _ = res_mgr.record_result(final_m["id"], home_score=3, away_score=2)
    assert ok_f is True

    champ_m = db.execute_one("SELECT winner_team_id FROM matches WHERE bracket_slot = 'F';")
    assert champ_m["winner_team_id"] == final_m["home_team_id"]

    # 9. Master Workbook Export
    master_xlsx = tmp_dir / "master_report.xlsx"
    exp_svc.export_full_tournament_workbook(master_xlsx)
    assert master_xlsx.exists() and master_xlsx.stat().st_size > 0

    # 10. Database Backup and Safety Restore
    backup_file = backup_svc.create_backup(label="integration_final")
    assert backup_file.exists()

    # Reset data
    backup_svc.reset_tournament_data()
    assert db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"] == 0

    # Restore from backup
    restored, _ = backup_svc.restore_backup(backup_file)
    assert restored is True
    assert db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"] > 0
