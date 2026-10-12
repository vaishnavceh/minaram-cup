"""
Tests for FastAPI Backend API, Public Data Privacy, and Admin Security.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from app.database import Database
from app.backup_service import BackupService

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_tournament_data_and_preserve():
    db = Database()
    backup_svc = BackupService(db)
    # Save current live database state
    snapshot = backup_svc.create_backup("pytest_session_snapshot")
    # Generate test sample tournament
    backup_svc.generate_sample_tournament()
    yield
    # Restore exact state
    backup_svc.restore_backup(snapshot)
    if snapshot.exists():
        try:
            snapshot.unlink()
        except Exception:
            pass


def test_public_tournament_summary():
    resp = client.get("/api/public/tournament")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Minaram Cup"
    assert data["edition"] == "2026 Edition"
    assert data["stats"]["teams_count"] == 8
    assert data["stats"]["total_matches"] > 0
    assert "eligibility" in data


def test_public_teams_privacy_enforcement():
    """Verify that public endpoints NEVER expose phone numbers or private notes."""
    resp = client.get("/api/public/teams")
    assert resp.status_code == 200
    teams = resp.json()
    assert len(teams) > 0
    for t in teams:
        assert "phone_number" not in t, "Security Violation: Phone number leaked in public endpoint!"
        assert "raw_message" not in t
        assert "notes" not in t
        assert "name" in t
        assert "stats" in t


def test_public_standings():
    resp = client.get("/api/public/standings")
    assert resp.status_code == 200
    standings = resp.json()
    assert "Group A" in standings
    assert "Group B" in standings
    assert len(standings["Group A"]) == 4
    for r in standings["Group A"]:
        assert "points" in r
        assert "goal_difference" in r
        assert "rank" in r


def test_public_bracket():
    resp = client.get("/api/public/bracket")
    assert resp.status_code == 200
    bracket = resp.json()
    assert "Semi-Final" in bracket or "Final" in bracket


def test_admin_endpoints_require_authentication():
    """Verify that all write and private endpoints reject unauthenticated requests."""
    # Attempt to view private registrations with phone numbers
    resp_regs = client.get("/api/admin/registrations")
    assert resp_regs.status_code == 401

    # Attempt to add a team without auth
    resp_team = client.post("/api/admin/teams", json={"name": "Hacker FC"})
    assert resp_team.status_code == 401

    # Attempt to enter match score without auth
    resp_res = client.post("/api/admin/matches/1/result", json={"home_score": 5, "away_score": 0})
    assert resp_res.status_code == 401


def test_admin_login_and_authenticated_operations():
    # Login with valid credentials (JSON)
    login_resp = client.post("/api/admin/login", json={"username": "admin", "password": "minaram2026"})
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]
    assert token is not None
    assert login_resp.json()["access_token"] == token

    # Form URL-encoded login as used by the website Admin portal
    form_resp = client.post("/api/admin/auth/token", data={"username": "admin", "password": "minaram2026"})
    assert form_resp.status_code == 200
    assert form_resp.json()["access_token"] is not None
    assert form_resp.json()["token_type"] == "bearer"

    headers = {"Authorization": f"Bearer {token}"}

    # Verify protected access with token
    health_resp = client.get("/api/admin/health", headers=headers)
    assert health_resp.status_code == 200


    # Test automatic registration-to-team creation via admin
    reg_data = {
        "participant_name": "Test Star Player",
        "phone_number": "9998887776",
        "team_name": "Automatic Team FC",
        "status": "Confirmed"
    }
    create_resp = client.post("/api/admin/registrations", json=reg_data, headers=headers)
    assert create_resp.status_code == 200

    # Verify team was created and is visible in public teams
    public_teams_resp = client.get("/api/public/teams")
    names = [t["name"] for t in public_teams_resp.json()]
    assert "Automatic Team FC" in names


def test_spa_frontend_serving():
    """Verify that root and client-side routes serve the built index.html."""
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "MINARAM CUP" in resp_root.text

    resp_spa_route = client.get("/fixtures")
    assert resp_spa_route.status_code == 200
    assert "MINARAM CUP" in resp_spa_route.text


def test_static_asset_serving():
    """Verify that processed transparent logos and backgrounds are served correctly."""
    resp_logo = client.get("/assets/logos/transparent/minaram_logo_white.png")
    assert resp_logo.status_code == 200
    assert resp_logo.headers["content-type"] in ["image/png", "image/x-png"]

    resp_bg = client.get("/assets/backgrounds/bg_stadium_cinematic.webp")
    assert resp_bg.status_code == 200
    assert resp_bg.headers["content-type"] in ["image/webp"]
