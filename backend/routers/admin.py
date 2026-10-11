"""
Private Admin API Endpoints for Minaram Cup.
Protected with Bearer token authentication.
Allows authorized administrators to manage registrations, teams, fixtures, and results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status, File, UploadFile
from pydantic import BaseModel

from app.database import Database
from app.registration_service import RegistrationService
from app.team_manager import TeamManager
from app.tournament_manager import TournamentManager
from app.fixture_generator import FixtureGenerator
from app.knockout_manager import KnockoutManager
from app.results_manager import ResultsManager
from app.backup_service import BackupService
from app.standings import StandingsCalculator
from backend.auth import get_current_admin, create_access_token, ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

db = Database()
reg_svc = RegistrationService(db)
team_mgr = TeamManager(db)
tourn_mgr = TournamentManager(db)
fix_gen = FixtureGenerator(db)
ko_mgr = KnockoutManager(db)
res_mgr = ResultsManager(db)
stand_calc = StandingsCalculator(db)
backup_svc = BackupService(db)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegistrationCreate(BaseModel):
    participant_name: str
    phone_number: str
    team_name: str
    status: Optional[str] = "Confirmed"
    notes: Optional[str] = ""


class TeamCreate(BaseModel):
    name: str
    captain_name: Optional[str] = ""
    phone_number: Optional[str] = ""
    status: Optional[str] = "Confirmed"
    group_id: Optional[int] = None
    seed: Optional[int] = 0
    notes: Optional[str] = ""


class ResultEntry(BaseModel):
    home_score: int
    away_score: int
    status: Optional[str] = "Completed"
    home_penalty: Optional[int] = None
    away_penalty: Optional[int] = None
    walkover_winner_id: Optional[int] = None
    notes: Optional[str] = ""


class StandingsOverrideRequest(BaseModel):
    team_id: int
    played: Optional[int] = None
    won: Optional[int] = None
    drawn: Optional[int] = None
    lost: Optional[int] = None
    goals_for: Optional[int] = None
    goals_against: Optional[int] = None
    points: Optional[int] = None
    notes: Optional[str] = ""


# ----------------------------------------------------
# Authentication
# ----------------------------------------------------
@router.post("/login")
def login_admin(req: LoginRequest):
    if req.username != ADMIN_USERNAME or req.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = create_access_token(req.username)
    return {"token": token, "username": req.username, "role": "admin"}


@router.get("/me")
def get_current_user_info(admin: dict = Depends(get_current_admin)):
    return {"username": admin["sub"], "role": admin["role"]}


@router.get("/health")
def get_admin_health(admin: dict = Depends(get_current_admin)):
    return {
        "status": "healthy",
        "database": str(db.db_path),
        "registrations": db.execute_one("SELECT COUNT(*) AS c FROM registrations;")["c"],
        "teams": db.execute_one("SELECT COUNT(*) AS c FROM teams;")["c"],
        "matches": db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"],
    }


# ----------------------------------------------------
# Registrations Management (Protected)
# ----------------------------------------------------
@router.get("/registrations")
def get_admin_registrations(admin: dict = Depends(get_current_admin)):
    regs = reg_svc.get_registrations()
    return [r.to_dict() for r in regs]


@router.post("/registrations")
def create_registration_admin(req: RegistrationCreate, admin: dict = Depends(get_current_admin)):
    reg_id = reg_svc.add_registration_manual(
        name=req.participant_name,
        phone=req.phone_number,
        team_name=req.team_name,
        status=req.status or "Confirmed",
        notes=req.notes or ""
    )
    return {"status": "created", "registration_id": reg_id}


@router.delete("/registrations/{reg_id}")
def delete_registration_admin(reg_id: int, admin: dict = Depends(get_current_admin)):
    reg_svc.delete_registration(reg_id)
    return {"status": "deleted", "registration_id": reg_id}


@router.post("/registrations/parse")
def parse_registration_text_endpoint(raw_text: str = Body(..., embed=True), admin: dict = Depends(get_current_admin)):
    previews = reg_svc.preview_raw_text(raw_text)
    return {"items": previews}


@router.post("/registrations/save-batch")
def save_registration_batch(items: List[Dict[str, Any]] = Body(...), admin: dict = Depends(get_current_admin)):
    saved_cnt, errors = reg_svc.save_parsed_registrations(items, auto_confirm=True)
    return {"saved_count": saved_cnt, "errors": errors}


@router.post("/registrations/reconcile")
def reconcile_registrations_admin(admin: dict = Depends(get_current_admin)):
    reconciled = reg_svc.reconcile_registrations_to_teams()
    return {"reconciled_count": reconciled}


# ----------------------------------------------------
# Teams Management (Protected)
# ----------------------------------------------------
@router.post("/teams")
def create_team_admin(req: TeamCreate, admin: dict = Depends(get_current_admin)):
    try:
        t_id = team_mgr.create_team(
            name=req.name,
            captain_name=req.captain_name or "",
            phone_number=req.phone_number or "",
            status=req.status or "Confirmed",
            group_id=req.group_id,
            seed=req.seed or 0,
            notes=req.notes or ""
        )
        return {"status": "created", "team_id": t_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/teams/{team_id}")
def delete_team_admin(team_id: int, admin: dict = Depends(get_current_admin)):
    ok, msg = team_mgr.delete_team(team_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "deleted", "message": msg}


@router.post("/teams/merge")
def merge_teams_admin(source_id: int = Body(...), target_id: int = Body(...), admin: dict = Depends(get_current_admin)):
    ok, msg = team_mgr.merge_teams(source_id, target_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "merged", "message": msg}


# ----------------------------------------------------
# Groups & Fixtures Management (Protected)
# ----------------------------------------------------
@router.post("/groups")
def create_group_admin(name: str = Body(..., embed=True), admin: dict = Depends(get_current_admin)):
    try:
        g_id = tourn_mgr.create_group(name)
        return {"status": "created", "group_id": g_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/groups/distribute")
def distribute_groups_admin(randomize: bool = Body(False), admin: dict = Depends(get_current_admin)):
    try:
        alloc = tourn_mgr.preview_team_distribution(randomize=randomize, seed_aware=True)
        tourn_mgr.apply_group_allocation(alloc)
        return {"status": "applied", "allocation": alloc}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fixtures/generate")
def generate_fixtures_admin(
    format_type: str = Body("Group Stage"),
    start_date: str = Body(""),
    start_time: str = Body("09:00"),
    duration_mins: int = Body(30),
    day_end_time: str = Body("19:00"),
    venue: str = Body("Minaram Pitch 1, Minaram Pitch 2"),
    clear_existing: bool = Body(True),
    admin: dict = Depends(get_current_admin)
):
    try:
        venue_list = [v.strip() for v in venue.split(",") if v.strip()] or ["Minaram Stadium"]
        if "Knockout" in format_type:
            fixtures = ko_mgr.generate_bracket_from_group_qualifiers(
                start_date=start_date, start_time=start_time, match_duration_mins=duration_mins, venue=venue_list[0]
            )
        elif "League" in format_type:
            fixtures = fix_gen.preview_league_fixtures(
                start_date=start_date, start_time=start_time, match_duration_mins=duration_mins, venues=venue_list, day_end_time=day_end_time
            )
        else:
            fixtures = fix_gen.preview_group_fixtures(
                start_date=start_date, start_time=start_time, match_duration_mins=duration_mins, venues=venue_list, day_end_time=day_end_time
            )

        saved_cnt = fix_gen.save_fixtures(fixtures, clear_existing=clear_existing)
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("fixtures_updated", {"count": saved_cnt})
        return {"status": "generated", "saved_count": saved_cnt}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ----------------------------------------------------
# Match Results Management (Protected)
# ----------------------------------------------------
@router.post("/matches/{match_id}/result")
def enter_match_result_admin(match_id: int, req: ResultEntry, admin: dict = Depends(get_current_admin)):
    ok, msg = res_mgr.record_result(
        match_id=match_id,
        home_score=req.home_score,
        away_score=req.away_score,
        status=req.status or "Completed",
        home_penalty=req.home_penalty,
        away_penalty=req.away_penalty,
        walkover_winner_id=req.walkover_winner_id,
        notes=req.notes or ""
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "saved", "message": msg}


@router.delete("/matches/{match_id}/result")
def reset_match_result_admin(match_id: int, reason: str = Body("Admin Reset"), admin: dict = Depends(get_current_admin)):
    ok, msg = res_mgr.reset_result(match_id, reason=reason)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "reset", "message": msg}


# ----------------------------------------------------
# Standings & Points Table Overrides (Protected)
# ----------------------------------------------------
@router.get("/standings/overrides")
def get_standings_overrides_admin(admin: dict = Depends(get_current_admin)):
    return stand_calc.get_overrides()


@router.post("/standings/overrides")
def set_standings_override_admin(req: StandingsOverrideRequest, admin: dict = Depends(get_current_admin)):
    stand_calc.set_team_override(
        team_id=req.team_id,
        played=req.played,
        won=req.won,
        drawn=req.drawn,
        lost=req.lost,
        goals_for=req.goals_for,
        goals_against=req.goals_against,
        points=req.points,
        notes=req.notes or ""
    )
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("standings_updated", {"team_id": req.team_id})
    return {"status": "saved", "message": f"Override applied for team #{req.team_id}. Standings auto-reordered."}


@router.delete("/standings/overrides/{team_id}")
def clear_team_override_admin(team_id: int, admin: dict = Depends(get_current_admin)):
    stand_calc.clear_team_override(team_id)
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("standings_updated", {"team_id": team_id})
    return {"status": "cleared", "message": f"Override cleared for team #{team_id}."}


@router.delete("/standings/overrides")
def clear_all_standings_overrides_admin(admin: dict = Depends(get_current_admin)):
    stand_calc.clear_all_overrides()
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("standings_updated", {})
    return {"status": "cleared", "message": "All standings overrides cleared."}


# ----------------------------------------------------
# Maintenance & Demo (Protected)
# ----------------------------------------------------
@router.post("/sample-data")
def generate_sample_tournament_admin(admin: dict = Depends(get_current_admin)):
    try:
        backup_svc.generate_sample_tournament()
        return {"status": "generated", "message": "Sample tournament created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
def reset_tournament_admin(admin: dict = Depends(get_current_admin)):
    backup_svc.reset_tournament_data()
    return {"status": "reset", "message": "All tournament data cleared."}


# ----------------------------------------------------
# Cloud Sync Operations (Protected)
# ----------------------------------------------------
@router.get("/sync/download-database")
def download_database_admin(admin: dict = Depends(get_current_admin)):
    """Export the authoritative SQLite database for local desktop backup or sync."""
    from fastapi.responses import FileResponse
    if not db.db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")
    return FileResponse(
        path=str(db.db_path),
        filename="minaram_cup.db",
        media_type="application/x-sqlite3"
    )


@router.post("/sync/upload-database")
async def upload_database_admin(
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    """
    Import/Publish the local desktop SQLite database to the cloud server.
    Takes an automatic safety backup on the server, verifies database integrity,
    and broadcasts a live update event to all connected web clients.
    """
    from app.events import broadcaster
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Only .db SQLite database files are accepted")

    content = await file.read()
    if len(content) < 100 or not content.startswith(b"SQLite format 3"):
        raise HTTPException(status_code=400, detail="Invalid SQLite database file header")

    # 1. Take safety backup on server before replacing
    try:
        backup_svc.create_backup("pre_cloud_sync_safety")
    except Exception:
        pass

    # 2. Write new database
    with open(db.db_path, "wb") as f:
        f.write(content)

    # 3. Broadcast live update to website
    broadcaster.broadcast_from_thread("standings_updated", {"source": "cloud_sync"})

    return {
        "status": "synchronized",
        "message": f"Cloud database updated successfully ({len(content)} bytes). Live website updated."
    }

