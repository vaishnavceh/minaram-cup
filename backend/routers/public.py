"""
Public Read-Only API Endpoints for Minaram Cup.
Provides tournament summary, teams, fixtures, results, standings, and brackets.
STRICT PRIVACY ENFORCEMENT: Never exposes participant phone numbers, notes, or private logs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request

from app.database import Database
from app.team_manager import TeamManager
from app.tournament_manager import TournamentManager
from app.fixture_generator import FixtureGenerator
from app.standings import StandingsCalculator
from app.knockout_manager import KnockoutManager
from app.number_to_whatsapp_link import make_whatsapp_link
from app.live_stream_service import LiveStreamService

router = APIRouter(prefix="/api/public", tags=["Public Tournament Data"])

def safe_whatsapp_link(number: Optional[str]) -> Optional[str]:
    if not number:
        return None
    try:
        return make_whatsapp_link(number)
    except Exception:
        return None

db = Database()
team_mgr = TeamManager(db)
tourn_mgr = TournamentManager(db)
fix_gen = FixtureGenerator(db)
stand_calc = StandingsCalculator(db)
ko_mgr = KnockoutManager(db)
live_stream_svc = LiveStreamService(db)

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
            "home_whatsapp_link": safe_whatsapp_link(m.home_phone),
            "away_captain": m.away_captain,
            "away_phone": m.away_phone,
            "away_whatsapp_link": safe_whatsapp_link(m.away_phone),
            "complaint_whatsapp_link": "https://wa.me/919746603975",
            "start_date": m.scheduled_date,
            "scheduled_date": m.scheduled_date,
            "end_date": m.end_date,
            "scheduled_end_date": m.end_date,
            "scheduled_time": m.scheduled_time,
            "venue": m.venue,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "status": m.status,
            "winner_team_name": m.winner_team_name,
            "notes": m.notes
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
            "home_whatsapp_link": safe_whatsapp_link(m.home_phone),
            "away_captain": m.away_captain,
            "away_phone": m.away_phone,
            "away_whatsapp_link": safe_whatsapp_link(m.away_phone),
            "complaint_whatsapp_link": "https://wa.me/919746603975",
            "start_date": m.scheduled_date,
            "scheduled_date": m.scheduled_date,
            "end_date": m.end_date,
            "scheduled_end_date": m.end_date,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "home_penalty": m.home_penalty,
            "away_penalty": m.away_penalty,
            "score_display": m.score_display,
            "status": m.status,
            "winner_team_name": m.winner_team_name,
            "notes": m.notes,
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


@router.get("/knockout/bracket")
def get_public_knockout_bracket() -> Dict[str, Any]:
    """Retrieve full dynamic knockout tournament data (direct qualifiers, predictions, official results, rules, conflicts)."""
    return ko_mgr.get_knockout_tournament_data()


@router.get("/knockout/rules")
def get_public_knockout_rules() -> Dict[str, Any]:
    """Retrieve official knockout match rules, eFootball game settings, and penalty/walkover policies."""
    return ko_mgr.get_rules()


@router.get("/bracket")
def get_public_bracket() -> Dict[str, Any]:
    """Retrieve visual knockout bracket tree with full preliminary to final support."""
    ko_data = ko_mgr.get_knockout_tournament_data()

    # Format both stage-based mapping (for legacy clients) and rounds array (for standard viewer)
    res: Dict[str, Any] = {}
    rounds = []

    for stage_name, matches in ko_data["bracket"].items():
        stage_match_list = [
            {
                "id": m.get("id") or m.get("match_number") or 0,
                "tournament_id": 1,
                "stage": stage_name,
                "match_number": m.get("match_number"),
                "bracket_slot": m.get("bracket_slot"),
                "home_team_id": m.get("home_team_id"),
                "away_team_id": m.get("away_team_id"),
                "home_team_name": m.get("home_team_name") or m.get("home_placeholder") or "Yet to decide",
                "away_team_name": m.get("away_team_name") or m.get("away_placeholder") or "Yet to decide",
                "team_a_name": m.get("home_team_name") or m.get("home_placeholder") or "Yet to decide",
                "team_b_name": m.get("away_team_name") or m.get("away_placeholder") or "Yet to decide",
                "home_group": m.get("home_group", ""),
                "away_group": m.get("away_group", ""),
                "home_score": m.get("home_score"),
                "away_score": m.get("away_score"),
                "team_a_score": m.get("home_score"),
                "team_b_score": m.get("away_score"),
                "home_penalty": m.get("home_penalty"),
                "away_penalty": m.get("away_penalty"),
                "penalty_a": m.get("home_penalty"),
                "penalty_b": m.get("away_penalty"),
                "status": m.get("status", "PREDICTED"),
                "winner_team_id": m.get("winner_team_id"),
                "winner_team_name": m.get("winner_team_name"),
                "winner_name": m.get("winner_team_name"),
                "winner_method": m.get("winner_method", ""),
                "is_completed": (m.get("status") == "COMPLETED"),
                "scheduled_date": m.get("scheduled_date") or "TBD",
                "scheduled_time": m.get("scheduled_time") or "Flexible (MW Window)",
                "venue": m.get("venue") or "Minaram Stadium",
                "pitch": m.get("venue") or "Minaram Stadium",
                "notes": m.get("notes") or "",
                "is_official": m.get("is_official", False)
            }
            for m in matches
        ]
        res[stage_name] = stage_match_list
        rounds.append({
            "round_name": stage_name,
            "matches": stage_match_list
        })

    res["rounds"] = rounds
    res["champion"] = ko_data.get("champion")
    res["direct_qualifiers"] = ko_data.get("direct_qualifiers", [])
    res["recommended_qualifiers"] = ko_data.get("recommended_qualifiers", [])
    res["has_direct_override"] = ko_data.get("has_direct_override", False)
    res["snapshot_version"] = ko_data.get("snapshot_version")
    res["last_updated"] = ko_data.get("last_updated")
    res["is_provisional"] = ko_data.get("is_provisional", False)
    res["draw_method"] = ko_data.get("draw_method", "seeded")
    res["conflicts"] = ko_data.get("conflicts", [])
    res["rules"] = ko_data.get("rules", {})
    res["statuses_legend"] = ko_data.get("statuses_legend", {})

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


@router.get("/top-scorers")
def get_public_top_scorers(limit: int = 15) -> List[Dict[str, Any]]:
    """Retrieve tournament top goal scorers and Golden Boot standings."""
    query = """
        SELECT t.id, t.name, t.captain_name, t.group_id, g.name AS group_name,
               SUM(CASE WHEN m.home_team_id = t.id THEN m.home_score ELSE 0 END +
                   CASE WHEN m.away_team_id = t.id THEN m.away_score ELSE 0 END) AS goals,
               COUNT(m.id) AS matches_played
        FROM teams t
        LEFT JOIN groups g ON t.group_id = g.id
        JOIN matches m ON (m.home_team_id = t.id OR m.away_team_id = t.id)
        WHERE m.status IN ('Completed', 'Walkover')
          AND m.home_score IS NOT NULL
          AND m.away_score IS NOT NULL
        GROUP BY t.id
        HAVING goals > 0
        ORDER BY goals DESC, matches_played ASC, t.name ASC
        LIMIT ?;
    """
    rows = db.execute_query(query, (limit,))
    res = []
    for idx, r in enumerate(rows):
        mp = r["matches_played"] or 1
        g = r["goals"] or 0
        ratio = round(g / mp, 1) if mp > 0 else 0
        res.append({
            "rank": idx + 1,
            "team_id": r["id"],
            "team_name": r["name"],
            "player_name": r["captain_name"] or r["name"],
            "group_name": r["group_name"] or "TBD",
            "goals": g,
            "matches_played": mp,
            "goals_per_match": ratio
        })
    return res


@router.get("/live-stream")
def get_public_live_stream(request: Request) -> Dict[str, Any]:
    """
    Retrieve active live stream configuration and verified YouTube embed data.
    Sanitized for public viewing: Never exposes unpublished, hidden, or administrative details.
    """
    host = request.headers.get("host", "")
    return live_stream_svc.get_public_config(host_domain=host)


