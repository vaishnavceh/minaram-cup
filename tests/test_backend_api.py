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


def test_live_events_broadcaster():
    """Verify that EventBroadcaster publishes real-time events with both type and event keys."""
    import json
    from app.events import broadcaster

    q = broadcaster.subscribe()
    broadcaster.broadcast("knockout_updated", entity_id=1, data={"action": "test_broadcast"})
    assert not q.empty()
    msg = q.get_nowait()
    broadcaster.unsubscribe(q)

    data = json.loads(msg)
    assert data["type"] == "knockout_updated"
    assert data["event"] == "knockout_updated"
    assert data["data"]["action"] == "test_broadcast"


def test_new_admin_login():
    """Verify that new admin vaishnavvfisc@gmail.com can log in and access protected endpoints."""
    # 1. JSON login
    json_resp = client.post("/api/admin/login", json={"username": "vaishnavvfisc@gmail.com", "password": "popcorncinema@1"})
    assert json_resp.status_code == 200
    token = json_resp.json()["access_token"]
    assert token is not None

    # 2. Form login
    form_resp = client.post("/api/admin/auth/token", data={"username": "vaishnavvfisc@gmail.com", "password": "popcorncinema@1"})
    assert form_resp.status_code == 200
    assert form_resp.json()["access_token"] is not None

    # 3. Access protected health endpoint
    headers = {"Authorization": f"Bearer {token}"}
    health_resp = client.get("/api/admin/health", headers=headers)
    assert health_resp.status_code == 200


def test_draw_apply_and_reset_workflow():
    """Verify applying ceremonial draw moves fixtures to knockout, and reset wipes clean."""
    # 1. Admin login
    form_resp = client.post("/api/admin/auth/token", data={"username": "admin", "password": "minaram2026"})
    assert form_resp.status_code == 200
    token = form_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Reset any previous test fixtures to ensure clean initial un-drawn state
    client.post("/api/admin/knockout/reset-draw", headers=headers)
    b_resp = client.get("/api/public/knockout/bracket")
    assert b_resp.status_code == 200
    rounds = b_resp.json().get("rounds", [])
    if rounds:
        for r in rounds:
            for m in r.get("matches", []):
                assert m.get("is_published") is False
                assert m.get("team_a_name") == "Yet to decide"

    # 3. Apply custom ceremonial draw pairings with real team IDs
    teams_resp = client.get("/api/public/teams")
    assert teams_resp.status_code == 200
    teams_list = teams_resp.json()
    assert len(teams_list) >= 4
    t1, t2, t3, t4 = [t["id"] for t in teams_list[:4]]

    pairings = [
        {"match_number": 1, "home_team_id": t1, "away_team_id": t2},
        {"match_number": 2, "home_team_id": t3, "away_team_id": t4},
    ]
    apply_resp = client.post(
        "/api/admin/knockout/apply-draw",
        json={"pairings": pairings, "status_mode": "CONFIRMED"},
        headers=headers
    )
    assert apply_resp.status_code == 200
    assert apply_resp.json()["status"] == "applied"
    assert apply_resp.json()["count"] >= 2

    # 4. Check bracket has published fixtures
    b_after = client.get("/api/public/knockout/bracket")
    assert b_after.status_code == 200
    rounds_after = b_after.json().get("rounds", [])
    pr_round = next((r for r in rounds_after if "preliminary" in r["round_name"].lower()), None)
    assert pr_round is not None
    m1 = next((m for m in pr_round["matches"] if m.get("bracket_slot") == "PR1"), None)
    assert m1 is not None
    assert m1.get("is_published") is True

    # 5. Reset ceremonial draw: verify complete rollback of all knockout fixtures
    reset_resp = client.post("/api/admin/knockout/reset-draw", headers=headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "reset"
    assert reset_resp.json()["rolled_back_count"] >= 2

    # 6. Verify clean state after reset
    b_clean = client.get("/api/public/knockout/bracket")
    assert b_clean.status_code == 200
    rounds_clean = b_clean.json().get("rounds", [])
    if rounds_clean:
        for r in rounds_clean:
            for m in r.get("matches", []):
                assert m.get("is_published") is False



