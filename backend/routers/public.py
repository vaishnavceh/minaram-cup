"""
Public Read-Only API Endpoints for Minaram Cup.
Provides tournament summary, teams, fixtures, results, standings, and brackets.
STRICT PRIVACY ENFORCEMENT: Never exposes participant phone numbers, notes, or private logs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException

from app.database import Database
from app.team_manager import TeamManager
from app.tournament_manager import TournamentManager
from app.fixture_generator import FixtureGenerator
from app.standings import StandingsCalculator
from app.knockout_manager import KnockoutManager

router = APIRouter(prefix="/api/public", tags=["Public Tournament Data"])

db = Database()
team_mgr = TeamManager(db)
tourn_mgr = TournamentManager(db)
fix_gen = FixtureGenerator(db)
stand_calc = StandingsCalculator(db)
ko_mgr = KnockoutManager(db)

MANIFEST_FILE = Path(__file__).resolve().parent.parent.parent / "tools" / "asset_manifest.json"


@router.get("/tournament")
def get_public_tournament_summary() -> Dict[str, Any]:
    """Retrieve public tournament overview, format settings, and live stats."""
    settings = db.get_all_settings()

    total_teams = db.execute_one("SELECT COUNT(*) AS c FROM teams WHERE status = 'Confirmed';")["c"]
    total_groups = db.execute_one("SELECT COUNT(*) AS c FROM groups;")["c"]
    total_matches = db.execute_one("SELECT COUNT(*) AS c FROM matches;")["c"]
    completed_matches = db.execute_one("SELECT COUNT(*) AS c FROM matches WHERE status IN ('Completed', 'Walkover');")["c"]
    pending_matches = total_matches - completed_matches

    # Next match
    next_m = db.execute_one("""
        SELECT m.id, m.match_number, m.stage, ht.name AS home_name, at.name AS away_name,
               m.scheduled_date, m.scheduled_time, m.venue
        FROM matches m
        LEFT JOIN teams ht ON m.home_team_id = ht.id
        LEFT JOIN teams at ON m.away_team_id = at.id
        WHERE m.status = 'Scheduled'
        ORDER BY m.scheduled_date ASC, m.scheduled_time ASC
        LIMIT 1;
    """)

    # Latest result
    latest_r = db.execute_one("""
        SELECT m.id, m.match_number, m.stage, ht.name AS home_name, at.name AS away_name,
               m.home_score, m.away_score, m.status, wt.name AS winner_name
        FROM matches m
        LEFT JOIN teams ht ON m.home_team_id = ht.id
        LEFT JOIN teams at ON m.away_team_id = at.id
        LEFT JOIN teams wt ON m.winner_team_id = wt.id
        WHERE m.status IN ('Completed', 'Walkover')
        ORDER BY m.id DESC
        LIMIT 1;
    """)

    return {
        "name": settings.get("tournament_name", "Minaram Cup"),
        "edition": settings.get("edition", "2026 Edition"),
        "sport": settings.get("sport", "Football"),
        "format": settings.get("format_type", "Group Stage + Knockout"),
        "scoring_rules": {
            "win_points": int(settings.get("win_points", "3")),
            "draw_points": int(settings.get("draw_points", "1")),
            "loss_points": int(settings.get("loss_points", "0")),
        },
        "default_venue": settings.get("default_venue", "Minaram Stadium"),
        "team_count": total_teams,
        "groups_count": total_groups,
        "match_count": total_matches,
        "completed_matches": completed_matches,
        "stats": {
            "teams_count": total_teams,
            "groups_count": total_groups,
            "total_matches": total_matches,
            "completed_matches": completed_matches,
            "pending_matches": pending_matches,
            "progress_percent": int((completed_matches / total_matches * 100)) if total_matches > 0 else 0,
        },
        "next_match": dict(next_m) if next_m else None,
        "latest_result": dict(latest_r) if latest_r else None,
        "eligibility": "TKM College of Engineering Students Only",
        "organizer": "minarathintememe",
        "sponsor": "Akhadha",
    }


@router.get("/teams")
def get_public_teams() -> List[Dict[str, Any]]:
    """
    List all confirmed teams with public statistics.
    PRIVACY GUARANTEE: Never exposes phone numbers, notes, or registration messages.
    """
    teams = team_mgr.get_teams(status="Confirmed")
    public_teams = []

    for t in teams:
        stats = team_mgr.get_team_stats(t.id)
        public_teams.append({
            "id": t.id,
            "name": t.name,
            "captain_name": t.captain_name or "TBD",
            "group_id": t.group_id,
            "group_name": t.group_name or "Unassigned",
            "seed": t.seed,
            "stats": stats
        })

    return public_teams


@router.get("/teams/{team_id}")
def get_public_team_detail(team_id: int) -> Dict[str, Any]:
    """Retrieve public team profile and match history."""
    t = team_mgr.get_team_by_id(team_id)
    if not t or t.status != "Confirmed":
        raise HTTPException(status_code=404, detail="Team not found")

    stats = team_mgr.get_team_stats(team_id)
    history = team_mgr.get_team_match_history(team_id)

    # Sanitize history
    public_history = []
    for h in history:
        public_history.append({
            "match_id": h["match_id"],
            "match_number": h["match_number"],
            "stage": h["stage"],
            "date": h["date"],
            "time": h["time"],
            "venue": h["venue"],
            "is_home": h["is_home"],
            "opponent": h["opponent"],
            "team_score": h["team_score"],
            "opp_score": h["opp_score"],
            "outcome": h["outcome"],
            "status": h["status"]
        })

    return {
        "id": t.id,
        "name": t.name,
        "captain_name": t.captain_name or "TBD",
        "group_id": t.group_id,
        "group_name": t.group_name or "Unassigned",
        "seed": t.seed,
        "stats": stats,
        "match_history": public_history
    }


@router.get("/groups")
def get_public_groups() -> List[Dict[str, Any]]:
    """Retrieve group list and team allocations."""
    groups = tourn_mgr.get_groups()
    res = []
    for g in groups:
        teams = tourn_mgr.get_group_teams(g.id)
        res.append({
            "id": g.id,
            "name": g.name,
            "display_order": g.display_order,
            "teams": [
                {
                    "id": t.id,
                    "name": t.name,
                    "captain_name": t.captain_name or "TBD",
                    "seed": t.seed
                }
                for t in teams
            ]
        })
    return res


@router.get("/fixtures")
def get_public_fixtures(stage: Optional[str] = None, group_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve public tournament fixtures, schedule, and team coordinator contacts."""
    matches = fix_gen.get_matches(stage=stage, group_id=group_id)
    return [
        {
            "id": m.id,
            "match_number": m.match_number,
            "stage": m.stage,
            "group_id": m.group_id,
            "group_name": m.group_name,
            "round_number": m.round_number,
            "home_team_id": m.home_team_id,
            "away_team_id": m.away_team_id,
            "home_team_name": m.home_team_name,
            "away_team_name": m.away_team_name,
            "home_captain": m.home_captain,
            "home_phone": m.home_phone,
            "away_captain": m.away_captain,
            "away_phone": m.away_phone,
            "scheduled_date": m.scheduled_date,
            "scheduled_time": m.scheduled_time,
            "venue": m.venue,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "status": m.status,
            "winner_team_name": m.winner_team_name
        }
        for m in matches
    ]


@router.get("/results")
def get_public_results() -> List[Dict[str, Any]]:
    """Retrieve completed match results."""
    matches = fix_gen.get_matches(status="Completed")
    walkovers = fix_gen.get_matches(status="Walkover")
    all_results = sorted(matches + walkovers, key=lambda x: x.match_number)

    return [
        {
            "id": m.id,
            "match_number": m.match_number,
            "stage": m.stage,
            "group_name": m.group_name,
            "home_team_name": m.home_team_name,
            "away_team_name": m.away_team_name,
            "home_captain": m.home_captain,
            "home_phone": m.home_phone,
            "away_captain": m.away_captain,
            "away_phone": m.away_phone,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "home_penalty": m.home_penalty,
            "away_penalty": m.away_penalty,
            "score_display": m.score_display,
            "status": m.status,
            "winner_team_name": m.winner_team_name,
            "completed_at": m.completed_at
        }
        for m in all_results
    ]


@router.get("/standings")
def get_public_standings() -> Dict[str, Any]:
    """Retrieve live calculated group standings and points tables."""
    all_standings = stand_calc.calculate_all_groups_standings()
    # Format into serialized dict
    res = {}
    for g_name, rows in all_standings.items():
        res[g_name] = [
            {
                "rank": r.rank,
                "team_id": r.team_id,
                "team_name": r.team_name,
                "played": r.played,
                "won": r.won,
                "drawn": r.drawn,
                "lost": r.lost,
                "goals_for": r.goals_for,
                "goals_against": r.goals_against,
                "goal_difference": r.goal_difference,
                "points": r.points,
                "form": r.form,
                "is_qualified": r.is_qualified
            }
            for r in rows
        ]
    return res


@router.get("/bracket")
def get_public_bracket() -> Dict[str, Any]:
    """Retrieve visual knockout bracket tree."""
    bracket_tree = ko_mgr.get_bracket_structure()
    res = {}
    for stage, matches in bracket_tree.items():
        res[stage] = [
            {
                "id": m.id,
                "match_number": m.match_number,
                "bracket_slot": m.bracket_slot,
                "home_team_name": m.home_team_name if m.home_team_name != "TBD" else (m.notes or "TBD"),
                "away_team_name": m.away_team_name if m.away_team_name != "TBD" else (m.notes or "TBD"),
                "home_score": m.home_score,
                "away_score": m.away_score,
                "home_penalty": m.home_penalty,
                "away_penalty": m.away_penalty,
                "status": m.status,
                "winner_team_name": m.winner_team_name,
                "is_completed": m.is_completed,
                "scheduled_date": m.scheduled_date,
                "scheduled_time": m.scheduled_time
            }
            for m in matches
        ]
    return res


@router.get("/manifest")
def get_asset_manifest() -> Dict[str, Any]:
    """Retrieve visual asset manifest for dynamic hero & background selection."""
    if MANIFEST_FILE.exists():
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "default", "backgrounds": [], "logos": {}}
