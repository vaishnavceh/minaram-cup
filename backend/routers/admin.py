"""
Private Admin API Endpoints for Minaram Cup.
Protected with Bearer token authentication.
Allows authorized administrators to manage registrations, teams, fixtures, and results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status, File, UploadFile, Form
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
from backend.auth import get_current_admin, create_access_token, authenticate_admin, ADMIN_USERNAME, ADMIN_PASSWORD

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
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    team_a_score: Optional[int] = None
    team_b_score: Optional[int] = None
    status: Optional[str] = "Completed"
    home_penalty: Optional[int] = None
    away_penalty: Optional[int] = None
    penalty_a: Optional[int] = None
    penalty_b: Optional[int] = None
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


class KnockoutResultRequest(BaseModel):
    home_score: int
    away_score: int
    home_penalty: Optional[int] = None
    away_penalty: Optional[int] = None
    winner_team_id: Optional[int] = None
    winner_method: Optional[str] = "Regular Time"
    notes: Optional[str] = ""


class KnockoutStatusRequest(BaseModel):
    status: str
    notes: Optional[str] = ""


class KnockoutWalkoverRequest(BaseModel):
    winner_team_id: int
    reason: str


class KnockoutEditFixtureRequest(BaseModel):
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    scheduled_date: Optional[str] = ""
    scheduled_time: Optional[str] = ""
    venue: Optional[str] = ""
    notes: Optional[str] = ""


class KnockoutDirectOverrideRequest(BaseModel):
    slot_index: int
    team_id: int
    reason: str


class KnockoutDrawConfigRequest(BaseModel):
    draw_method: str  # "seeded" or "random"


class KnockoutRuleUpdateRequest(BaseModel):
    key: str
    value: str


class ThirdPlaceToggleRequest(BaseModel):
    enabled: bool


# ----------------------------------------------------
# Authentication
# ----------------------------------------------------
@router.post("/auth/token")
def login_admin_form(
    username: str = Form(...),
    password: str = Form(...)
):
    """OAuth2 / URL-encoded form login used by website Admin Portal."""
    admin_user = authenticate_admin(username, password, db)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(admin_user["username"])
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "username": admin_user["username"],
        "role": admin_user.get("role", "admin")
    }


@router.post("/login")
def login_admin_json(req: LoginRequest):
    """JSON login for programmatic clients."""
    admin_user = authenticate_admin(req.username, req.password, db)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    token = create_access_token(admin_user["username"])
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "username": admin_user["username"],
        "role": admin_user.get("role", "admin")
    }



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
    end_date: str = Body(""),
    days_per_matchweek: int = Body(3),
    start_time: str = Body("16:00"),
    duration_mins: int = Body(30),
    day_end_time: str = Body("20:00"),
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
                start_date=start_date, start_time=start_time, match_duration_mins=duration_mins,
                venues=venue_list, day_end_time=day_end_time, end_date=end_date, days_per_matchweek=days_per_matchweek
            )
        else:
            fixtures = fix_gen.preview_group_fixtures(
                start_date=start_date, start_time=start_time, match_duration_mins=duration_mins,
                venues=venue_list, day_end_time=day_end_time, end_date=end_date, days_per_matchweek=days_per_matchweek
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
    h_score = req.home_score if req.home_score is not None else req.team_a_score
    a_score = req.away_score if req.away_score is not None else req.team_b_score
    if h_score is None or a_score is None:
        raise HTTPException(status_code=400, detail="Both home and away scores are required")
    h_pen = req.home_penalty if req.home_penalty is not None else req.penalty_a
    a_pen = req.away_penalty if req.away_penalty is not None else req.penalty_b

    ok, msg = res_mgr.record_result(
        match_id=match_id,
        home_score=h_score,
        away_score=a_score,
        status=req.status or "Completed",
        home_penalty=h_pen,
        away_penalty=a_pen,
        walkover_winner_id=req.walkover_winner_id,
        notes=req.notes or ""
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "saved", "message": msg}


@router.post("/matches/{match_id}/reset")
@router.delete("/matches/{match_id}/result")
def reset_match_result_admin(match_id: int, reason: str = Body("Admin Reset"), admin: dict = Depends(get_current_admin)):
    ok, msg = res_mgr.reset_result(match_id, reason=reason)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "reset", "message": msg}


@router.post("/tournament/advance-stage")
def advance_tournament_stage_admin(admin: dict = Depends(get_current_admin)):
    """Advance tournament from completed group stage to knockout rounds."""
    try:
        fixtures = ko_mgr.generate_bracket_from_group_qualifiers()
        if not fixtures:
            raise HTTPException(status_code=400, detail="Cannot advance stage: group standings are not completed yet.")
        saved_cnt = fix_gen.save_fixtures(fixtures, clear_existing=False)
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("fixtures_updated", {"count": saved_cnt})
        broadcaster.broadcast_from_thread("standings_updated", {})
        return {"status": "advanced", "message": f"Successfully advanced tournament stage! Generated {saved_cnt} knockout fixtures."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



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


# ----------------------------------------------------
# Knockout Tournament Management (Protected)
# ----------------------------------------------------
@router.post("/knockout/recalculate")
def recalculate_knockout_predictions_admin(admin: dict = Depends(get_current_admin)):
    """Recalculate predicted qualifiers and knockout fixtures from latest group standings."""
    try:
        snap = ko_mgr.get_or_create_predicted_snapshot(force=True)
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "recalculated", "version": snap["version"]})
        return {
            "status": "recalculated",
            "version": snap["version"],
            "last_updated": snap["created_at"],
            "is_provisional": snap["is_provisional"],
            "message": "Knockout predictions updated from latest standings."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knockout/preview")
def preview_knockout_admin(admin: dict = Depends(get_current_admin)):
    """Preview master knockout tournament data (predictions, direct qualifiers, official results)."""
    return ko_mgr.get_knockout_tournament_data()


@router.post("/knockout/draw-config")
def update_draw_config_admin(req: KnockoutDrawConfigRequest, admin: dict = Depends(get_current_admin)):
    """Update draw configuration (seeded vs random) and regenerate predictions."""
    if req.draw_method not in ("seeded", "random"):
        raise HTTPException(status_code=400, detail="draw_method must be 'seeded' or 'random'")
    ko_mgr.update_rule("draw_method", req.draw_method, admin_username=admin["sub"])
    snap = ko_mgr.get_or_create_predicted_snapshot(force=True, draw_method=req.draw_method)
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("knockout_updated", {"action": "draw_config_updated"})
    return {"status": "updated", "draw_method": req.draw_method, "version": snap["version"]}


@router.post("/knockout/direct-qualifiers/override")
def override_direct_qualifier_admin(req: KnockoutDirectOverrideRequest, admin: dict = Depends(get_current_admin)):
    """Manually assign or replace one of the two direct Round of 16 qualifiers."""
    try:
        res = ko_mgr.set_direct_qualifier_override(
            slot_index=req.slot_index,
            team_id=req.team_id,
            reason=req.reason,
            admin_username=admin["sub"]
        )
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "direct_qualifier_overridden"})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/knockout/direct-qualifiers/override")
def clear_direct_qualifier_override_admin(admin: dict = Depends(get_current_admin)):
    """Clear manual direct qualifier overrides and restore automatically calculated recommendations."""
    res = ko_mgr.clear_direct_qualifier_overrides(admin_username=admin["sub"])
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("knockout_updated", {"action": "direct_overrides_cleared"})
    return res


@router.post("/knockout/fixtures/{bracket_slot}/confirm")
def confirm_fixture_admin(bracket_slot: str, admin: dict = Depends(get_current_admin)):
    """Officially approve a predicted fixture into the authoritative tournament bracket."""
    try:
        res = ko_mgr.confirm_fixture(bracket_slot, admin_username=admin["sub"])
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "fixture_confirmed", "bracket_slot": bracket_slot})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/fixtures/batch-confirm")
def batch_confirm_stage_admin(stage: str = Body(..., embed=True), admin: dict = Depends(get_current_admin)):
    """Batch approve all predicted fixtures of a stage into official bracket."""
    try:
        cnt = ko_mgr.batch_confirm_stage(stage, admin_username=admin["sub"])
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "batch_confirmed", "stage": stage})
        return {"status": "confirmed", "stage": stage, "count": cnt}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/fixtures/{bracket_slot}/unconfirm")
def unconfirm_fixture_admin(bracket_slot: str, admin: dict = Depends(get_current_admin)):
    """Revert an unplayed official fixture back to predicted."""
    try:
        res = ko_mgr.unconfirm_fixture(bracket_slot, admin_username=admin["sub"])
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "fixture_unconfirmed", "bracket_slot": bracket_slot})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/knockout/fixtures/{bracket_slot}")
def edit_fixture_admin(bracket_slot: str, req: KnockoutEditFixtureRequest, admin: dict = Depends(get_current_admin)):
    """Edit teams, schedule, or venue for an official knockout fixture."""
    try:
        res = ko_mgr.edit_fixture(
            bracket_slot=bracket_slot,
            home_team_id=req.home_team_id,
            away_team_id=req.away_team_id,
            scheduled_date=req.scheduled_date or "",
            scheduled_time=req.scheduled_time or "",
            venue=req.venue or "",
            notes=req.notes or "",
            admin_username=admin["sub"]
        )
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "fixture_edited", "bracket_slot": bracket_slot})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/fixtures/{bracket_slot}/result")
def record_knockout_result_admin(bracket_slot: str, req: KnockoutResultRequest, admin: dict = Depends(get_current_admin)):
    """Record final score, determine winner, advance winner to next designated slot, mark loser eliminated."""
    try:
        res = ko_mgr.record_knockout_result(
            bracket_slot=bracket_slot,
            home_score=req.home_score,
            away_score=req.away_score,
            home_penalty=req.home_penalty,
            away_penalty=req.away_penalty,
            winner_team_id=req.winner_team_id,
            winner_method=req.winner_method or "Regular Time",
            notes=req.notes or "",
            admin_username=admin["sub"]
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/fixtures/{bracket_slot}/status")
def set_fixture_status_admin(bracket_slot: str, req: KnockoutStatusRequest, admin: dict = Depends(get_current_admin)):
    """Update fixture status (LIVE, UNDER REVIEW, CONFIRMED)."""
    try:
        res = ko_mgr.set_fixture_status(
            bracket_slot=bracket_slot,
            status=req.status,
            notes=req.notes or "",
            admin_username=admin["sub"]
        )
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "status_updated", "bracket_slot": bracket_slot})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/fixtures/{bracket_slot}/walkover")
def record_walkover_admin(bracket_slot: str, req: KnockoutWalkoverRequest, admin: dict = Depends(get_current_admin)):
    """Record an official walkover with policy documentation."""
    try:
        res = ko_mgr.record_walkover(
            bracket_slot=bracket_slot,
            winner_team_id=req.winner_team_id,
            reason=req.reason,
            admin_username=admin["sub"]
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/rules")
def update_knockout_rule_admin(req: KnockoutRuleUpdateRequest, admin: dict = Depends(get_current_admin)):
    """Update a knockout rule or game setting."""
    rules = ko_mgr.update_rule(req.key, req.value, admin_username=admin["sub"])
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("knockout_updated", {"action": "rule_updated"})
    return {"status": "saved", "rules": rules}


@router.post("/knockout/rules/third-place-toggle")
def toggle_third_place_admin(req: ThirdPlaceToggleRequest, admin: dict = Depends(get_current_admin)):
    """Enable or disable third-place playoff."""
    res = ko_mgr.toggle_third_place(req.enabled, admin_username=admin["sub"])
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("knockout_updated", {"action": "third_place_toggled", "enabled": req.enabled})
    return res


@router.post("/knockout/reset-predictions")
def reset_predictions_admin(admin: dict = Depends(get_current_admin)):
    """Reset unconfirmed prediction snapshots without touching confirmed or completed fixtures."""
    res = ko_mgr.reset_unconfirmed_predictions(admin_username=admin["sub"])
    from app.events import broadcaster
    broadcaster.broadcast_from_thread("knockout_updated", {"action": "predictions_reset"})
    return res


@router.get("/knockout/audit-log")
def get_knockout_audit_log_admin(limit: int = 100, admin: dict = Depends(get_current_admin)):
    """View administrative audit trail of all knockout actions."""
    return ko_mgr.get_audit_logs(limit=limit)


@router.post("/knockout/apply-draw")
def apply_ceremonial_draw_admin(
    pairings: list = Body(..., embed=True),
    status_mode: str = Body("CONFIRMED", embed=True),
    admin: dict = Depends(get_current_admin)
):
    """Apply administrator's UEFA ceremonial draw pairings to official knockout fixtures."""
    try:
        res = ko_mgr.apply_custom_draw(pairings=pairings, admin_username=admin["sub"], status_mode=status_mode, clear_existing=True)
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "ceremonial_draw_applied", "status_mode": status_mode})
        broadcaster.broadcast_from_thread("ceremonial_draw_applied", {"status_mode": status_mode})
        broadcaster.broadcast_from_thread("fixtures_updated", {})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/reset-draw")
def reset_ceremonial_draw_admin(admin: dict = Depends(get_current_admin)):
    """Reset ceremonial draw and roll back all published preliminary knockout fixtures."""
    try:
        res = ko_mgr.reset_ceremonial_draw(admin_username=admin["sub"])
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "ceremonial_draw_reset"})
        broadcaster.broadcast_from_thread("ceremonial_draw_reset", {})
        broadcaster.broadcast_from_thread("fixtures_updated", {})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/clear-fixtures")
def clear_knockout_fixtures_admin(
    mode: str = Body("ALL", embed=True),
    admin: dict = Depends(get_current_admin)
):
    """Clear published knockout fixtures by mode ('ALL', 'PREDICTED', 'CONFIRMED')."""
    try:
        res = ko_mgr.clear_knockout_fixtures(mode=mode, admin_username=admin["sub"])
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "knockout_fixtures_cleared", "mode": mode})
        broadcaster.broadcast_from_thread("ceremonial_draw_reset", {})
        broadcaster.broadcast_from_thread("fixtures_updated", {})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/set-fixtures-status")
def set_knockout_fixtures_status_admin(
    stage: str = Body("Preliminary Round", embed=True),
    status_mode: str = Body("CONFIRMED", embed=True),
    admin: dict = Depends(get_current_admin)
):
    """Batch toggle published fixtures of a stage between CONFIRMED and PREDICTED."""
    try:
        res = ko_mgr.batch_set_stage_status(stage=stage, status_mode=status_mode, admin_username=admin["sub"])
        from app.events import broadcaster
        broadcaster.broadcast_from_thread("knockout_updated", {"action": "fixtures_status_updated", "status_mode": status_mode})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knockout/sync-desktop")
def sync_draw_to_desktop_admin(admin: dict = Depends(get_current_admin)):
    """Export and sync official knockout draw directly to Desktop."""
    try:
        res = ko_mgr.export_draw_to_desktop(admin_username=admin["sub"])
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

